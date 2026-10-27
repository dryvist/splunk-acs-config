#!/usr/bin/env python3
"""Pull, plan, push, copy and document Splunk Cloud ACS settings stored as TOML files."""

import argparse
import json
import os
import re
import sys
import time
from collections import Counter
from pathlib import Path
import tomllib
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from pipeline.output import color_line, pipeline_message

PAGE_SIZE = 100
POLL_INTERVAL = 10
POLL_ATTEMPTS = 90  # 15 minutes at one poll per POLL_INTERVAL
META = ("environments", "overrides", "unset", "push")
FEATURES = ("s2s", "hec", "search-ui", "search-api", "idm-api", "idm-ui", "acs", "federated-search")
# Built-in roles the tool never reads or writes.
BUILTIN_ROLES = ("admin", "can_delete", "power", "sc_admin", "splunk-system-role", "user")

def ip_type(feature_list):
    return {"key": "feature", "fields": ("feature", "subnets"), "subnet": True, "keys": FEATURES,
            "list": f"/access/{{key}}/{feature_list}", "items": ("subnets",),
            "post": f"/access/{{key}}/{feature_list}", "delete": f"/access/{{key}}/{feature_list}"}


def outbound_type(prefix):
    return {"key": "port", "fields": ("port", "subnets", "reason"), "patch_fields": ("subnets",),
            "subnet": True, "list": f"/access/{prefix}", "items": (),
            "post": f"/access/{prefix}", "delete": f"/access/{prefix}/{{key}}"}


TYPES = {
    "indexes": {
        "key": "name",
        "fields": ("name", "datatype", "mdlIndex", "maxDataSizeMB", "searchableDays",
                   "selfStorageBucketPath", "splunkArchivalRetentionDays"),
        "patch_fields": ("maxDataSizeMB", "searchableDays", "selfStorageBucketPath",
                         "splunkArchivalRetentionDays"),
        # ACS OpenAPI IndexInfo defaults.
        "splunk_defaults": {"datatype": "event", "maxDataSizeMB": 0, "searchableDays": 90},
        "list": "/indexes", "items": ("indexes",), "paged": True,
        "post": "/indexes", "patch": "/indexes/{key}", "delete": "/indexes/{key}", "push": True,
    },
    "hec-tokens": {
        "key": "name",
        "fields": ("name", "_meta", "allowedIndexes", "defaultHost", "defaultIndex",
                   "defaultSource", "defaultSourcetype", "disabled", "useAck"),
        # inputs.conf.spec [http://<name>], Splunk 10.6.
        "splunk_defaults": {"disabled": False, "useAck": False},
        "list": "/inputs/http-event-collectors", "items": ("http_event_collectors",), "paged": True,
        "post": "/inputs/http-event-collectors", "patch": "/inputs/http-event-collectors/{key}",
        "delete": "/inputs/http-event-collectors/{key}", "push": True,
    },
    "ip-allowlists": ip_type("ipallowlists"),
    "ip-allowlists-v6": ip_type("ipallowlists-v6"),
    "outbound-ports": outbound_type("outbound-ports"),
    "outbound-ports-v6": outbound_type("outbound-ports-v6"),
    "roles": {
        "key": "name",
        "fields": ("name", "capabilities", "cumulativeRTSrchJobsQuota", "cumulativeSrchJobsQuota",
                   "defaultApp", "importedRoles", "rtSrchJobsQuota", "srchDiskQuota", "srchFilter",
                   "srchIndexesAllowed", "srchIndexesDefault", "srchJobsQuota", "srchTimeEarliest",
                   "srchTimeWin"),
        # authorize.conf [default], Splunk 10.6. The cumulative quotas are not in the ACS
        # OpenAPI RolesInfo schema, so no default is set for them.
        "splunk_defaults": {"srchDiskQuota": 100, "srchJobsQuota": 3, "rtSrchJobsQuota": 6},
        "list": "/roles", "items": ("roles",), "paged": True, "skip": BUILTIN_ROLES,
        "post": "/roles", "patch": "/roles/{key}", "delete": "/roles/{key}",
    },
    "limits": {
        "key": "stanza", "fields": None, "list": "/limits", "items": (),
        "post": "/limits/{key}",
    },
    "app-permissions": {
        "key": "name", "fields": ("name", "read", "write", "owner"),
        "patch_fields": ("read", "write"), "repo_only": ("owner",),
        "list": "/permissions/apps", "items": ("apps",), "paged": True,
        "patch": "/permissions/apps/{key}", "push": True,
    },
    "private-apps": {
        "key": "name", "fields": ("name", "version"),
        "list": "/apps/victoria?splunkbase=false&count=0", "items": ("apps",), "push": False,
    },
    "splunkbase-apps": {
        "key": "name", "fields": ("name", "id", "version", "license"), "patch_fields": ("version",),
        "repo_only": ("license",),
        "list": "/apps/victoria?splunkbase=true&count=0", "items": ("apps",),
        "post": "/apps/victoria?splunkbase=true", "patch": "/apps/victoria/{key}", "push": True,
    },
}


def type_fields(t, *items):
    fields = TYPES[t]["fields"]
    return fields if fields is not None else tuple(sorted(set().union(*(i.keys() for i in items))))


for _type, _spec in TYPES.items():
    _fields = type_fields(_type)
    if _fields:
        _spec.setdefault("patch_fields", tuple(f for f in _fields if f != _spec["key"]))


class ACSConfigError(Exception):
    pass


def env_value(name):
    value = os.environ.get(name, "")
    return "" if re.fullmatch(r"\$\([^)]*\)", value) else value


def api_base():
    stack = env_value("SPLUNK_STACK")
    if not stack:
        raise ACSConfigError("SPLUNK_STACK is not set")
    search_head = env_value("SPLUNK_SEARCH_HEAD")
    host = f"{search_head}.{stack}" if search_head else stack
    return f"https://admin.splunk.com/{host}/adminconfig/v2"


def request(method, path, body=None, form=False, extra_headers=None):
    external = path.startswith("https://")
    token = env_value("STACK_TOKEN") or env_value("ACS_TOKEN")
    if not external and not token:
        raise ACSConfigError("STACK_TOKEN or ACS_TOKEN is not set")
    url = path if external else api_base() + path
    data = None if body is None else (
        urlencode(body).encode("utf-8") if form else json.dumps(body).encode("utf-8"))
    headers = {"Accept": "application/json",
               "Content-Type": "application/x-www-form-urlencoded" if form else "application/json"}
    if not external:
        headers["Authorization"] = f"Bearer {token}"
    headers.update(extra_headers or {})
    try:
        with urlopen(Request(url, data=data, method=method, headers=headers), timeout=60) as resp:
            status, text = resp.status, resp.read().decode("utf-8")
    except HTTPError as err:
        message = err.reason
        try:
            message = json.loads(err.read()).get("message") or message
        except (ValueError, AttributeError):
            pass
        err.close()
        raise ACSConfigError(f"HTTP {err.code} {method} {url}: {message}") from None
    except URLError as err:
        raise ACSConfigError(f"{method} {url}: {err.reason}") from None
    except UnicodeDecodeError as err:
        raise ACSConfigError(f"invalid UTF-8 response from {method} {url}: {err}") from None
    try:
        data = text if external else (json.loads(text) if text.strip() else None)
    except json.JSONDecodeError as err:
        raise ACSConfigError(f"invalid JSON from {method} {url}: {err}") from None
    return data, status


def read_toml(path, default=None):
    if not path.exists():
        return default
    try:
        with path.open("rb") as file:
            return tomllib.load(file)
    except (tomllib.TOMLDecodeError, UnicodeDecodeError) as err:
        raise ACSConfigError(f"{path}: {err}") from None


def store(root, path, text):
    old = path.read_text(encoding="utf-8") if path.exists() else None
    if old == text:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    print(color_line(f"{'changed' if old is not None else 'created'} {path.relative_to(root)}"))
    return True


def toml_key(key):
    return key if re.fullmatch(r"[A-Za-z0-9_-]+", key) else json.dumps(key)


def toml_value(value):
    if isinstance(value, (str, bool)):
        return json.dumps(value)
    if isinstance(value, int):
        return str(value)
    if isinstance(value, list) and all(type(v) in (str, int) for v in value):
        return "[" + ", ".join(toml_value(v) for v in value) + "]"
    raise ACSConfigError(f"unsupported TOML value: {value!r}")


def dump_toml(data, dotted=False):
    lines = []

    def write_table(table, path=()):
        scalars = [key for key, value in table.items() if not isinstance(value, dict)]
        children = [key for key, value in table.items() if isinstance(value, dict)]
        stanza = dotted and len(path) == 1
        if path and (scalars or not children or path == ("default",) or stanza):
            lines.extend([""] if lines else [])
            lines.append(f"[{'.'.join(map(toml_key, path))}]")
        first = next((key for key in ("name", "feature", "port")
                      if not path and key in scalars), None)
        meta = [key for key in ("environments", "push", "unset") if key in scalars]
        keys = ([first] if first else []) + meta + sorted(key for key in scalars
                                                          if key != first and key not in meta)
        lines.extend(f"{toml_key(key)} = {toml_value(table[key])}" for key in keys)
        if stanza:
            for env in sorted(children):
                lines.extend(f"{toml_key(env)}.{toml_key(field)} = {toml_value(value)}"
                             for field, value in sorted(table[env].items()))
        else:
            for key in sorted(children, key=lambda key: (path == () and key != "default", key)):
                write_table(table[key], (*path, key))

    write_table(data)
    return "\n".join(lines).rstrip() + "\n"


def load_environments(root):
    envs = read_toml(root / "environments.toml")
    if envs is None:
        raise ACSConfigError(f"missing {root / 'environments.toml'}")
    return envs


def env_types(envs, env):
    if env not in envs:
        raise ACSConfigError(f"unknown environment: {env}")
    return list(envs[env].get("types") or TYPES)


def select_types(raw, allowed):
    chosen = list(TYPES) if raw.strip() in ("", "all") else raw.split()
    unknown = [t for t in chosen if t not in TYPES]
    if unknown:
        raise ACSConfigError(f"unknown type: {' '.join(unknown)}")
    return [t for t in TYPES if t in chosen and t in allowed]


def select_names(raw):
    return None if raw.strip() in ("", "all") else set(raw.split())


def split_table(path, envs, name, table):
    fields, overrides = {}, {}
    for field, value in table.items():
        if not isinstance(value, dict):
            fields[field] = value
        elif field in envs:
            overrides[field] = value
        else:
            table_name = f"{toml_key(name)}.{toml_key(field)}"
            raise ACSConfigError(f"{path}: unknown environment table [{table_name}]")
    if overrides:
        fields["overrides"] = overrides
    return fields


def load_type(root, t, envs):
    path = root / "objects" / f"{t}.toml"
    data = read_toml(path, {})
    spec, objects = TYPES[t], {}
    defaults = data.pop("default", {})
    if not isinstance(defaults, dict):
        raise ACSConfigError(f"{path}: [default] must be a table")
    defaults = split_table(path, envs, "default", defaults)
    for name, table in data.items():
        if not isinstance(table, dict):
            raise ACSConfigError(f"{path}: stanza [{toml_key(name)}] must be a table")
        if name in spec.get("skip", ()):
            raise ACSConfigError(f"{path}: {name} is a built-in role and cannot be managed")
        raw = split_table(path, envs, name, table)
        if spec["key"] in raw:
            raise ACSConfigError(f"{path}: [{toml_key(name)}] cannot contain key field '{spec['key']}'")
        try:
            raw[spec["key"]] = int(name) if spec["key"] == "port" else name
        except ValueError:
            raise ACSConfigError(f"{path}: invalid port stanza [{toml_key(name)}]") from None
        key = str(raw[spec["key"]])
        if key in objects:
            raise ACSConfigError(f"{path}: duplicate {t} key {key}")
        objects[key] = raw
    return defaults, objects


def stanza(table, skip=()):
    out = {field: value for field, value in table.items() if field not in skip and field != "overrides"}
    out.update(table.get("overrides") or {})
    return out


def dump_type(t, defaults, objects):
    data = {"default": stanza(defaults)}
    for key, raw in sorted(objects.items()):
        data[key] = stanza(raw, (TYPES[t]["key"],))
    return dump_toml(data, dotted=True)


def store_type(root, t, defaults, objects):
    path = root / "objects" / f"{t}.toml"
    if objects or defaults or path.exists():
        return store(root, path, dump_type(t, defaults, objects))
    return False


def set_overrides(raw, overrides):
    if overrides:
        raw["overrides"] = overrides
    else:
        raw.pop("overrides", None)


def in_env(raw, env):
    return "environments" not in raw or env in raw["environments"]


def layers(t, defaults, raw, env, own_overrides=True):
    out = [TYPES[t].get("splunk_defaults", {}), defaults,
           (defaults.get("overrides") or {}).get(env) or {}, raw]
    if own_overrides:
        out.append((raw.get("overrides") or {}).get(env) or {})
    return out


def pushed(t, defaults, raw, env):
    flag = TYPES[t].get("push", False)
    for layer in layers(t, defaults, raw, env):
        flag = layer.get("push", flag)
    return flag


def merged(t, defaults, raw, env, own_overrides=True):
    eff = {}
    for layer in layers(t, defaults, raw, env, own_overrides):
        eff.update({k: v for k, v in layer.items() if k not in META})
        for k in layer.get("unset", ()):
            eff.pop(k, None)
    fields = type_fields(t, eff)
    unknown = sorted(set(eff) - set(fields))
    if unknown:
        raise ACSConfigError(f"{t}: unknown field(s) {', '.join(unknown)}")
    return {k: v for k, v in eff.items() if v is not None}


def canon(value):
    return sorted(value, key=str) if isinstance(value, list) else value


def normalize(t, item):
    if t == "hec-tokens":
        item = item.get("spec", item)
    elif t == "app-permissions":
        item = {"name": item["name"], **item.get("perms", {})}
    elif t == "limits":
        item = {"stanza": item["Stanza"], **item["Values"]}
    elif t == "roles":
        item = {**item, "importedRoles": (item.get("imported") or {}).get("roles")}
    elif t == "splunkbase-apps":
        item = {"name": item["name"], "id": item.get("splunkbaseID"), "version": item["version"]}
    elif t == "private-apps":
        item = {"name": item["name"], "version": item["version"]}
    elif t.startswith("outbound-ports"):
        item = {"port": item["port"], "subnets": item.get("destinationRanges")}
    fields = type_fields(t, item)
    return {k: canon(v) for k, v in item.items() if k in fields and v is not None}


def response_items(data, wrapper):
    if isinstance(data, list):
        return data
    for key in wrapper:
        found = [k for k in (key, key.replace("_", "-")) if isinstance(data, dict) and k in data]
        if not found:
            keys = ", ".join(data) if isinstance(data, dict) else type(data).__name__
            raise ACSConfigError(f"unexpected ACS response: no '{key}' list (found: {keys})")
        data = data[found[0]]
    return data or []


def paged_items(path, wrapper):
    items, offset = [], 0
    while True:
        data, _ = request("GET", f"{path}?count={PAGE_SIZE}&offset={offset}")
        page = response_items(data, wrapper)
        items += page
        if len(page) < PAGE_SIZE:
            return items
        offset += PAGE_SIZE


def path_for(template, key):
    return template.format(key=quote(str(key), safe=""))


def live_objects(t, names=None):
    spec = TYPES[t]
    key_field = spec["key"]
    if "keys" in spec:
        records = []
        for feature in spec["keys"]:
            if names is None or feature in names:
                try:
                    data, _ = request("GET", path_for(spec["list"], feature))
                except ACSConfigError as err:
                    warning(f"skipped {t}/{feature}: {err}")
                    continue
                records.append({key_field: feature,
                                "subnets": canon(response_items(data, spec["items"]))})
    else:
        if spec.get("paged"):
            items = paged_items(spec["list"], spec["items"])
        else:
            data, _ = request("GET", spec["list"])
            items = response_items(data, spec["items"])
        records = [normalize(t, item) for item in items]
    live = {}
    for record in records:
        key = str(record[key_field])
        if key == "default":
            raise ACSConfigError(f"{t}: live object 'default' is reserved")
        if key in spec.get("skip", ()) or (names is not None and key not in names):
            continue
        if spec.get("subnet") and not record.get("subnets"):
            continue
        live[key] = record
    return live


def change(t, key, op, **details):
    return {"type": t, "key": key, "op": op, **details}


def key_changes(t, key, eff, live):
    spec = TYPES[t]
    if spec.get("subnet"):
        have = set(live["subnets"]) if live else set()
        if eff is None:
            return [change(t, key, "ONLY LIVE", subnets=sorted(have))] if have else []
        want = set(eff.get("subnets", []))
        out = []
        if want - have:
            out.append(change(t, key, "ADD", subnets=sorted(want - have), eff=eff))
        if have - want:
            out.append(change(t, key, "REMOVE", subnets=sorted(have - want), eff=eff))
        return out
    if eff is None:
        return [change(t, key, "ONLY LIVE")]
    if live is None:
        if "post" not in spec:
            return [change(t, key, "MISSING")]
        return [change(t, key, "CREATE", eff=eff)]
    patch_fields = spec.get("patch_fields", tuple(f for f in type_fields(t, live, eff) if f != spec["key"]))
    fields = {f: (live.get(f), eff.get(f)) for f in patch_fields
              if canon(live.get(f)) != canon(eff.get(f))}
    return [change(t, key, "UPDATE", fields=fields, eff=eff)] if fields else []


def type_changes(root, env, t, names=None):
    """Plan only objects whose push flag is true; live-only objects follow the type's flag."""
    defaults, all_repo = load_type(root, t, load_environments(root))
    repo = {key: raw for key, raw in all_repo.items()
            if (names is None or key in names) and in_env(raw, env)}
    managed = {key for key, raw in repo.items() if pushed(t, defaults, raw, env)}
    type_pushed = pushed(t, defaults, {}, env)
    if not managed and not type_pushed:
        return []
    live = live_objects(t, names)
    keys = managed | ({k for k in live if k not in repo} if type_pushed else set())
    return [c for key in sorted(keys)
            for c in key_changes(t, key, merged(t, defaults, repo[key], env) if key in managed else None,
                                 live.get(key))]


def collect(root, env, types, names=None):
    return [c for t in types for c in type_changes(root, env, t, names)]


def describe(c):
    name, op = f"{c['type']}/{c['key']}", c["op"]
    if op == "CREATE":
        fields = [f for f in sorted(c["eff"]) if f != TYPES[c["type"]]["key"]]
        return [f"CREATE {name} fields: {', '.join(fields)}"]
    if op == "UPDATE":
        return [f"UPDATE {name} {f}: {json.dumps(live)} -> {json.dumps(repo)}"
                for f, (live, repo) in c["fields"].items()]
    if op in ("ADD", "REMOVE"):
        return [f"{op} SUBNETS {name}: {', '.join(c['subnets'])}"]
    if op == "ONLY LIVE":
        suffix = f": {', '.join(c['subnets'])}" if "subnets" in c else ""
        return [f"ONLY LIVE {name}{suffix}"]
    return [f"MISSING {name}: ACS has no create for this type"]


def show(changes, types, env):
    for t in types:
        print(pipeline_message("section", f"{t} (repo vs {env} live)"))
        for c in changes:
            if c["type"] == t:
                for line in describe(c):
                    print(color_line(line))
    print(color_line("NO DIFFERENCES" if not changes else f"{len(changes)} change(s)"))


def applicable(c, allow_delete):
    if c["op"] in ("CREATE", "UPDATE", "ADD"):
        return True
    if c["op"] == "REMOVE":
        return allow_delete
    if c["op"] == "ONLY LIVE":
        return allow_delete and "delete" in TYPES[c["type"]]
    return False


def add_body(t, key, c):
    if t.startswith("outbound-ports"):
        return {"outboundPorts": [{"port": int(key), "subnets": c["subnets"]}],
                "reason": c["eff"].get("reason", "")}
    return {"subnets": c["subnets"]}


def splunkbase_session():
    credentials = {"username": env_value("SPLUNKBASE_USERNAME"),
                  "password": env_value("SPLUNKBASE_PASSWORD")}
    if not all(credentials.values()):
        raise ACSConfigError("SPLUNKBASE_USERNAME and SPLUNKBASE_PASSWORD are required")
    data, _ = request("POST", "https://splunkbase.splunk.com/api/account:login", credentials, form=True)
    session = re.search(r"<id>([^<]+)</id>", data)
    if not session:
        raise ACSConfigError("Splunkbase login response has no session id")
    return session.group(1)


def apply_change(c, session=None):
    t, key, op, spec = c["type"], c["key"], c["op"], TYPES[c["type"]]
    if t == "limits" and op in ("CREATE", "UPDATE"):
        values = c["eff"] if op == "CREATE" else {field: repo for field, (_, repo) in c["fields"].items()}
        body = {"settings": {field: value for field, value in values.items() if field != spec["key"]}}
        return request("POST", path_for(spec["post"], key), body)[1]
    if t == "splunkbase-apps":
        body = ({"splunkbaseID": c["eff"]["id"], "version": c["eff"]["version"]}
                if op == "CREATE" else
                {field: repo for field, (_, repo) in c["fields"].items()})
        path = spec["post"] if op == "CREATE" else path_for(spec["patch"], key)
        headers = {"X-Splunkbase-Authorization": session}
        if c["eff"].get("license"):
            headers["ACS-Licensing-Ack"] = c["eff"]["license"]
        return request("POST" if op == "CREATE" else "PATCH", path, body, form=True,
                       extra_headers=headers)[1]
    if op == "CREATE":
        return request("POST", spec["post"], c["eff"])[1]
    if op == "UPDATE":
        body = {f: repo for f, (_, repo) in c["fields"].items()}
        return request("PATCH", path_for(spec["patch"], key), body)[1]
    if op == "ADD":
        return request("POST", path_for(spec["post"], key), add_body(t, key, c))[1]
    if op == "ONLY LIVE" and t == "indexes":
        print(color_line(f"DATA LOSS: deleting index {key} removes all of its data"))
    detail = f" subnets: {', '.join(c['subnets'])}" if "subnets" in c else ""
    print(color_line(f"DELETE {t}/{key}{detail}"))
    body = {"subnets": c["subnets"]} if "subnets" in c else None
    return request("DELETE", path_for(spec["delete"], key), body)[1]


def wait_converged(root, env, c, allow_delete):
    for _ in range(POLL_ATTEMPTS):
        pending = type_changes(root, env, c["type"], {c["key"]})
        if not any(applicable(p, allow_delete) for p in pending):
            return
        time.sleep(POLL_INTERVAL)
    raise ACSConfigError(f"timed out waiting for {c['type']}/{c['key']} to match the files")


def plan_command(root, env, types, names):
    changes = collect(root, env, types, names)
    show(changes, types, env)
    return changes


def push_command(root, env, types, names, allow_delete):
    changes = collect(root, env, types, names)
    show(changes, types, env)
    session = splunkbase_session() if any(c["type"] == "splunkbase-apps" and applicable(c, allow_delete)
                                          for c in changes) else None
    for c in changes:
        if applicable(c, allow_delete) and apply_change(c, session) == 202:
            wait_converged(root, env, c, allow_delete)
    left = collect(root, env, types, names)
    if left:
        raise ACSConfigError(f"{len(left)} differences remain after push")
    print(color_line("NO DIFFERENCES after push"))


def compact(t, defaults, values, keep):
    """Rebuild an object with the fewest lines that give each env its values; a tie keeps the base line."""
    key = TYPES[t]["key"]
    inherited = {env: merged(t, defaults, {}, env) for env in values}
    fields = (set().union(*(value.keys() for value in values.values())) |
              set().union(*(value.keys() for value in inherited.values()))) - {key}
    out = {field: value for field, value in keep.items() if field != "overrides"}
    overrides = {env: dict(value) for env, value in (keep.get("overrides") or {}).items()}
    unset = set()
    for field in sorted(fields):
        want = {env: canon(value.get(field)) for env, value in values.items()}
        base_values = {env: canon(value.get(field)) for env, value in inherited.items()}
        # Ties keep a base line, then the value of the env pulled first (reverse name order).
        order = sorted(values, reverse=True)
        choices = [(sum(base_values[env] != want[env] for env in values), 1, 0, "", False, None)]
        distinct = {json.dumps(value, sort_keys=True): value for value in want.values()}
        choices.extend((1 + sum(value != wanted for wanted in want.values()), 0,
                        min(i for i, env in enumerate(order) if want[env] == value), text, True, value)
                       for text, value in distinct.items())
        *_, set_base, base = min(choices)
        result = {env: base for env in values} if set_base else base_values
        if set_base:
            if base is None:
                unset.add(field)
            else:
                out[field] = base
        for env in values:
            if result[env] != want[env]:
                override = overrides.setdefault(env, {})
                if want[env] is None:
                    override.setdefault("unset", []).append(field)
                else:
                    override[field] = want[env]
    if unset:
        out["unset"] = sorted(unset)
    for value in overrides.values():
        if "unset" in value:
            value["unset"] = sorted(set(value["unset"]))
    overrides = {env: value for env, value in overrides.items() if value}
    if overrides:
        out["overrides"] = overrides
    return out


def common_values(t, live):
    key = TYPES[t]["key"]
    values = {}
    for field in type_fields(t, *live.values()):
        if field == key:
            continue
        counts = Counter(json.dumps(canon(raw.get(field)), sort_keys=True) for raw in live.values())
        if counts:
            value = json.loads(min(counts, key=lambda text: (-counts[text], text)))
            if value is not None:
                values[field] = value
    return values


def infer_defaults(t, defaults, env, live):
    if TYPES[t].get("subnet"):
        return
    common = common_values(t, live)
    builtins = TYPES[t].get("splunk_defaults", {})
    if not any(field not in META for field in defaults):
        defaults.update({f: v for f, v in common.items() if canon(v) != canon(builtins.get(f))})
    overrides = dict(defaults.get("overrides") or {})
    if env not in overrides:
        base = merged(t, defaults, {}, env, own_overrides=False)
        values = {f: v for f, v in common.items() if canon(v) != canon(base.get(f))}
        if values:
            overrides[env] = values
            set_overrides(defaults, overrides)


def pull_type(root, envs, env, t, names):
    spec = TYPES[t]
    defaults, repo = load_type(root, t, envs)
    live = live_objects(t, names)
    if names is None:
        infer_defaults(t, defaults, env, live)
    keys = set(live) | {k for k in repo if names is None or k in names}
    for key in sorted(keys):
        if key in live:
            existing = repo.get(key)
            if existing is None:
                object_envs = [env]
            elif "environments" in existing:
                object_envs = list(existing["environments"])
                if env not in object_envs:
                    object_envs.append(env)
            else:
                object_envs = list(envs)
            values = {e: {f: v for f, v in merged(t, defaults, existing, e).items()
                          if f != spec["key"]}
                      for e in object_envs if e != env}
            values[env] = {f: v for f, v in merged(t, defaults, existing or {}, env).items()
                           if f in spec.get("repo_only", ())}
            values[env].update({f: v for f, v in live[key].items() if f != spec["key"]})
            keep = {f: existing[f] for f in ("push",) if existing and f in existing}
            push_overrides = {e: {"push": value["push"]}
                              for e, value in (existing.get("overrides") or {}).items()
                              if "push" in value} if existing else {}
            if push_overrides:
                keep["overrides"] = push_overrides
            raw = compact(t, defaults, values, keep)
            if set(object_envs) == set(envs):
                raw.pop("environments", None)
            else:
                raw["environments"] = object_envs
            repo[key] = raw
        else:
            raw = repo[key]
            if in_env(raw, env):
                remaining = [e for e in raw.get("environments", envs) if e != env]
                if remaining:
                    raw["environments"] = remaining
                else:
                    del repo[key]
    store_type(root, t, defaults, repo)


def pull_command(root, envs, env, types, names):
    for t in types:
        print(pipeline_message("section", f"{t} ({env} live into repo)"))
        pull_type(root, list(envs), env, t, names)
    write_doc(root)


def copy_overrides(table, src, dst):
    overrides = dict(table.get("overrides") or {})
    if overrides.get(src):
        overrides[dst] = overrides[src]
    else:
        overrides.pop(dst, None)
    set_overrides(table, overrides)


def copy_command(root, src, dst, types, names):
    envs = load_environments(root)
    changed = False
    for t in types:
        print(pipeline_message("section", f"{t} (copy {src} to {dst})"))
        defaults, objects = load_type(root, t, envs)
        copy_overrides(defaults, src, dst)
        for key, raw in objects.items():
            if (names is not None and key not in names) or not in_env(raw, src):
                continue
            if "environments" in raw and dst not in raw["environments"]:
                raw["environments"].append(dst)
            copy_overrides(raw, src, dst)
        changed = store_type(root, t, defaults, objects) or changed
    if not changed:
        print("NO CHANGES")


def fmt(value):
    if isinstance(value, list):
        text = ", ".join(str(v) for v in value)
    elif isinstance(value, bool):
        text = "true" if value else "false"
    else:
        text = str(value)
    return (text or "(empty)").replace("|", "\\|")


def default_lines(t, defaults):
    lines = [f"- {field}: {fmt(value)} (Splunk default)"
             for field, value in TYPES[t].get("splunk_defaults", {}).items()]
    lines += [f"- {field}: {fmt(value)} ([default])" for field, value in defaults.items()
              if field not in META]
    for env, values in (defaults.get("overrides") or {}).items():
        lines += [f"- {field}: {fmt(value)} ({env}, [default])" for field, value in values.items()
                  if field not in META]
    return lines or ["- none"]


def write_doc(root):
    envs = load_environments(root)
    lines = ["# Splunk Cloud ACS configuration", "",
             "Each file in `objects/` holds one object type. `[default]` holds shared values; "
             "each stanza holds only what differs.", "",
             "| Type | File | Pushed by default | " + " | ".join(envs) + " |",
             "|" + " --- |" * (len(envs) + 3)]
    sections = []
    loaded = {}
    for t in TYPES:
        defaults, objects = load_type(root, t, envs)
        loaded[t] = (defaults, objects)
        counts = [str(sum(in_env(raw, env) for raw in objects.values()))
                  if t in env_types(envs, env) else "-" for env in envs]
        pushed_by_default = "yes" if pushed(t, defaults, {}, "") else "no"
        lines.append(f"| {t} | `objects/{t}.toml` | {pushed_by_default} | " + " | ".join(counts) + " |")
        sections += ["", f"## {t}", ""] + default_lines(t, defaults)
    sections += ["", "## apps", "", "| env | app | version | read | write | owner |",
                 "| --- | --- | --- | --- | --- | --- |"]
    for env in envs:
        allowed = env_types(envs, env)
        if "app-permissions" not in allowed:
            continue
        defaults, permissions = loaded["app-permissions"]
        versions = {}
        for t in ("private-apps", "splunkbase-apps"):
            if t not in allowed:
                continue
            type_defaults, objects = loaded[t]
            for name, raw in objects.items():
                if in_env(raw, env) and name not in versions:
                    version = merged(t, type_defaults, raw, env).get("version")
                    if version is not None:
                        versions[name] = version
        for name, raw in sorted(permissions.items()):
            if not in_env(raw, env):
                continue
            app = merged("app-permissions", defaults, raw, env)
            cells = (env, app["name"], versions.get(name), app.get("read"),
                     app.get("write"), app.get("owner"))
            sections.append("| " + " | ".join(fmt(value) if value is not None else ""
                                                   for value in cells) + " |")
    store(root, root / "README.md", "\n".join(lines + sections).rstrip() + "\n")


def error(message):
    print(color_line(pipeline_message("error", message)), file=sys.stderr)


def warning(message):
    print(color_line(pipeline_message("warning", message)))


def add_common(sub):
    sub.add_argument("--dir", default=".")
    sub.add_argument("--types", default="all")
    sub.add_argument("--names", default="all")


def build_parser():
    parser = argparse.ArgumentParser(description="Sync Splunk Cloud ACS settings with TOML files.")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("pull", "plan"):
        sub = commands.add_parser(name)
        sub.add_argument("env")
        if name == "plan":
            sub.add_argument("--check", action="store_true")
        add_common(sub)
    push = commands.add_parser("push")
    push.add_argument("env")
    push.add_argument("--delete", action="store_true")
    add_common(push)
    copy = commands.add_parser("copy")
    copy.add_argument("src")
    copy.add_argument("dst")
    add_common(copy)
    doc = commands.add_parser("doc")
    doc.add_argument("--dir", default=".")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    root = Path(args.dir)
    try:
        if args.command == "doc":
            write_doc(root)
            return 0
        envs = load_environments(root)
        if args.command == "copy":
            env_types(envs, args.src)
            types = select_types(args.types, env_types(envs, args.dst))
            copy_command(root, args.src, args.dst, types, select_names(args.names))
            return 0
        types = select_types(args.types, env_types(envs, args.env))
        names = select_names(args.names)
        if args.command == "pull":
            pull_command(root, envs, args.env, types, names)
        elif args.command == "plan":
            changes = plan_command(root, args.env, types, names)
            if args.check and changes:
                return 1
        else:
            push_command(root, args.env, types, names, args.delete)
    except (ACSConfigError, OSError, ValueError, KeyError) as err:
        error(str(err))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
