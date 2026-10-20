#!/usr/bin/env python3
"""Pull, plan, push, copy and document Splunk Cloud ACS settings stored as TOML files."""

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
import tomllib
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from pipeline.output import color_line, pipeline_message

PAGE_SIZE = 100
POLL_INTERVAL = 10
POLL_ATTEMPTS = 90  # 15 minutes at one poll per POLL_INTERVAL
META = ("environments", "overrides", "unset")
FEATURES = ("s2s", "hec", "search-ui", "search-api", "idm-api", "idm-ui", "acs", "federated-search")
# The OpenAPI spec does not list the built-in roles, so this list is unconfirmed.
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
        "list": "/indexes", "items": ("indexes",), "paged": True,
        "post": "/indexes", "patch": "/indexes/{key}", "delete": "/indexes/{key}",
    },
    "hec-tokens": {
        "key": "name",
        "fields": ("name", "_meta", "allowedIndexes", "defaultHost", "defaultIndex",
                   "defaultSource", "defaultSourcetype", "disabled", "useAck"),
        "list": "/inputs/http-event-collectors", "items": ("http_event_collectors",), "paged": True,
        "post": "/inputs/http-event-collectors", "patch": "/inputs/http-event-collectors/{key}",
        "delete": "/inputs/http-event-collectors/{key}",
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
        "list": "/roles", "items": ("roles",), "paged": True, "skip": BUILTIN_ROLES,
        "post": "/roles", "patch": "/roles/{key}", "delete": "/roles/{key}",
    },
    "app-permissions": {
        "key": "name", "fields": ("name", "read", "write"), "patch_fields": ("read", "write"),
        "list": "/permissions/apps", "items": ("apps",), "paged": True,
        "patch": "/permissions/apps/{key}",
    },
}


for _spec in TYPES.values():
    _spec.setdefault("patch_fields", tuple(f for f in _spec["fields"] if f != _spec["key"]))


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


def request(method, path, body=None):
    token = env_value("STACK_TOKEN") or env_value("ACS_TOKEN")
    if not token:
        raise ACSConfigError("STACK_TOKEN or ACS_TOKEN is not set")
    url = api_base() + path
    data = None if body is None else json.dumps(body).encode("utf-8")
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json",
               "Content-Type": "application/json"}
    try:
        with urlopen(Request(url, data=data, method=method, headers=headers), timeout=60) as resp:
            status, text = resp.status, resp.read().decode("utf-8")
    except HTTPError as err:
        message = err.reason
        try:
            message = json.loads(err.read()).get("message") or message
        except (ValueError, AttributeError):
            pass
        raise ACSConfigError(f"HTTP {err.code} {method} {url}: {message}") from None
    except URLError as err:
        raise ACSConfigError(f"{method} {url}: {err.reason}") from None
    except UnicodeDecodeError as err:
        raise ACSConfigError(f"invalid UTF-8 response from {method} {url}: {err}") from None
    try:
        data = json.loads(text) if text.strip() else None
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


def dump_toml(data):
    lines = []

    def write_table(table, path=()):
        scalars = [key for key, value in table.items() if not isinstance(value, dict)]
        children = [key for key, value in table.items() if isinstance(value, dict)]
        if path and (scalars or not children):
            lines.extend([""] if lines else [])
            lines.append(f"[{'.'.join(map(toml_key, path))}]")
        first = next((key for key in ("name", "feature", "port")
                      if not path and key in scalars), None)
        keys = ([first] if first else []) + sorted(key for key in scalars if key != first)
        lines.extend(f"{toml_key(key)} = {toml_value(table[key])}" for key in keys)
        for key in sorted(children):
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


def load_repo(root, t):
    spec, repo = TYPES[t], {}
    for path in sorted((root / "objects" / t).glob("*.toml")):
        if path.name == "_defaults.toml":
            continue
        raw = read_toml(path)
        if spec["key"] not in raw:
            raise ACSConfigError(f"{path}: missing key field '{spec['key']}'")
        key = str(raw[spec["key"]])
        if key in spec.get("skip", ()):
            raise ACSConfigError(f"{path}: {key} is a built-in role and cannot be managed")
        if key in repo:
            raise ACSConfigError(f"{path}: duplicate {t} key {key}")
        repo[key] = (path, raw)
    return repo


def load_defaults(root, t):
    return read_toml(root / "objects" / t / "_defaults.toml", {})


def set_overrides(raw, overrides):
    if overrides:
        raw["overrides"] = overrides
    else:
        raw.pop("overrides", None)


def in_env(raw, env):
    return "environments" not in raw or env in raw["environments"]


def merged(t, defaults, raw, env, own_overrides=True):
    layers = [defaults, (defaults.get("overrides") or {}).get(env) or {}, raw]
    if own_overrides:
        layers.append((raw.get("overrides") or {}).get(env) or {})
    eff = {}
    for layer in layers:
        eff.update({k: v for k, v in layer.items() if k not in META})
        for k in layer.get("unset", ()):
            eff.pop(k, None)
    unknown = sorted(set(eff) - set(TYPES[t]["fields"]))
    if unknown:
        raise ACSConfigError(f"{t}: unknown field(s) {', '.join(unknown)}")
    return {k: v for k, v in eff.items() if v is not None}


def repo_effective(root, t, env, names=None):
    defaults = load_defaults(root, t)
    return {key: merged(t, defaults, raw, env)
            for key, (_, raw) in load_repo(root, t).items()
            if (names is None or key in names) and in_env(raw, env)}


def canon(value):
    return sorted(value, key=str) if isinstance(value, list) else value


def normalize(t, item):
    if t == "hec-tokens":
        item = item.get("spec", item)
    elif t == "app-permissions":
        item = {"name": item["name"], **item.get("perms", {})}
    elif t == "roles":
        item = {**item, "importedRoles": (item.get("imported") or {}).get("roles")}
    elif t.startswith("outbound-ports"):
        item = {"port": item["port"], "subnets": item.get("destinationRanges")}
    return {k: canon(v) for k, v in item.items() if k in TYPES[t]["fields"] and v is not None}


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
                    message = pipeline_message("warning", f"skipped {t}/{feature}: {err}")
                    print(color_line(message))
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
    fields = {f: (live.get(f), eff.get(f)) for f in spec["patch_fields"]
              if canon(live.get(f)) != canon(eff.get(f))}
    return [change(t, key, "UPDATE", fields=fields)] if fields else []


def type_changes(root, env, t, names=None):
    effs = repo_effective(root, t, env, names)
    live = live_objects(t, names)
    changes = []
    for key in sorted(set(effs) | set(live)):
        changes += key_changes(t, key, effs.get(key), live.get(key))
    return changes


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


def show(changes, types):
    for t in types:
        print(pipeline_message("section", t))
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


def apply_change(c):
    t, key, op, spec = c["type"], c["key"], c["op"], TYPES[c["type"]]
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
    show(collect(root, env, types, names), types)


def push_command(root, env, types, names, allow_delete):
    changes = collect(root, env, types, names)
    show(changes, types)
    for c in changes:
        if applicable(c, allow_delete) and apply_change(c) == 202:
            wait_converged(root, env, c, allow_delete)
    left = collect(root, env, types, names)
    if left:
        raise ACSConfigError(f"{len(left)} differences remain after push")
    print("NO DIFFERENCES after push")


def pull_overrides(t, defaults, raw, env, live):
    base = merged(t, defaults, raw, env, own_overrides=False)
    overrides = dict(raw.get("overrides") or {})
    current = dict(overrides.get(env) or {})
    unset = set(current.pop("unset", []))
    for f in TYPES[t]["patch_fields"]:
        value = canon(live.get(f))
        unset.discard(f)
        current.pop(f, None)
        if value is None and f in base:
            unset.add(f)
        elif value != canon(base.get(f)):
            current[f] = value
    if unset:
        current["unset"] = sorted(unset)
    set_overrides(raw, {e: v for e, v in {**overrides, env: current}.items() if v})


def pull_type(root, envs, env, t, names):
    spec = TYPES[t]
    repo = load_repo(root, t)
    defaults = load_defaults(root, t)
    live = live_objects(t, names)
    keys = set(live) | {k for k in repo if names is None or k in names}
    for key in sorted(keys):
        if key in live:
            if key not in repo:
                fields = merged(t, defaults, {}, env)
                raw = {"environments": [env]}
                raw.update({f: v for f, v in live[key].items()
                            if f == spec["key"] or canon(v) != canon(fields.get(f))})
                store(root, root / "objects" / t / (re.sub(r"[/:]", "_", key) + ".toml"),
                      dump_toml(raw))
            else:
                path, raw = repo[key]
                if "environments" in raw and env not in raw["environments"]:
                    raw["environments"].append(env)
                pull_overrides(t, defaults, raw, env, live[key])
                store(root, path, dump_toml(raw))
        else:
            path, raw = repo[key]
            if in_env(raw, env):
                remaining = [e for e in raw.get("environments", envs) if e != env]
                if remaining:
                    raw["environments"] = remaining
                    store(root, path, dump_toml(raw))
                else:
                    path.unlink()
                    print(color_line(f"deleted {path.relative_to(root)}"))


def pull_command(root, envs, env, types, names):
    for t in types:
        pull_type(root, list(envs), env, t, names)
    write_doc(root)


def copy_command(root, src, dst, types, names):
    changed = False
    for t in types:
        for path in sorted((root / "objects" / t).glob("*.toml")):
            raw = read_toml(path)
            if path.name != "_defaults.toml":
                if names is not None and str(raw[TYPES[t]["key"]]) not in names:
                    continue
                if not in_env(raw, src):
                    continue
                if "environments" in raw and dst not in raw["environments"]:
                    raw["environments"].append(dst)
            overrides = dict(raw.get("overrides") or {})
            if overrides.get(src):
                overrides[dst] = overrides[src]
            else:
                overrides.pop(dst, None)
            set_overrides(raw, overrides)
            changed = store(root, path, dump_toml(raw)) or changed
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


def write_doc(root):
    envs = load_environments(root)
    lines = ["# Splunk Cloud ACS configuration", "",
             "Generated by `acs_config.py doc` from the files in `objects/`. "
             "Values are effective per environment.", ""]
    for t in TYPES:
        views = {e: repo_effective(root, t, e) if t in env_types(envs, e) else {} for e in envs}
        lines += [f"## {t}", ""]
        keys = sorted({k for view in views.values() for k in view})
        if not keys:
            lines += ["No objects.", ""]
            continue
        lines += ["| Object | Field | " + " | ".join(envs) + " |", "|" + " --- |" * (len(envs) + 2)]
        for key in keys:
            fields = sorted({f for view in views.values() if key in view for f in view[key]})
            for f in fields:
                cells = [fmt(views[e][key][f]) if f in views[e].get(key, {}) else "-" for e in envs]
                bold = len(set(cells)) > 1
                cells = [f"**{c}**" if bold and c != "-" else c for c in cells]
                lines.append(f"| {key} | {f} | " + " | ".join(cells) + " |")
        lines.append("")
    store(root, root / "README.md", "\n".join(lines).rstrip() + "\n")


def error(message):
    print(color_line(pipeline_message("error", message)), file=sys.stderr)


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
            plan_command(root, args.env, types, names)
        else:
            push_command(root, args.env, types, names, args.delete)
    except (ACSConfigError, OSError) as err:
        error(str(err))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
