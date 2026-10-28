"""Unit tests for acs_config.py. ACS is replaced by a fake request function; nothing touches the network."""

import contextlib
import copy
import csv
import io
import os
import shutil
import tempfile
import tomllib
import unittest
from pathlib import Path
from unittest import mock
from urllib.error import HTTPError

import acs_config

FIXTURE = Path(__file__).parent / "fixtures" / "base"
ENV = {"SPLUNK_STACK": "stack", "STACK_TOKEN": "token-value"}


class Seq:
    """A GET answer that is returned once per call, then the last item repeats."""

    def __init__(self, *items):
        self.items = list(items)

    def next(self):
        return self.items.pop(0) if len(self.items) > 1 else self.items[0]


class FakeACS:
    """GET answers come from routes; writes are recorded and return the given status."""

    def __init__(self, routes=None, status=None):
        self.routes = routes or {}
        self.status = status or {}
        self.calls = []

    def __call__(self, method, path, body=None):
        base = path.partition("?")[0]
        self.calls.append((method, base, body))
        if method != "GET":
            return None, self.status.get((method, base), 200)
        if (method, base) not in self.routes:
            raise AssertionError(f"unexpected GET {path}")
        value = self.routes[(method, base)]
        value = value.next() if isinstance(value, Seq) else value
        return copy.deepcopy(value), 200

    def writes(self):
        return [call for call in self.calls if call[0] != "GET"]


def index(name, **fields):
    base = {"name": name, "datatype": "event", "searchableDays": 90, "maxDataSizeMB": 0,
            "totalEventCount": "0", "totalRawSizeMB": "0"}
    return {**base, **fields}


class ACSTestCase(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name) / "config"
        shutil.copytree(FIXTURE, self.root)
        env = mock.patch.dict(os.environ, ENV, clear=True)
        env.start()
        self.addCleanup(env.stop)

    def run_cli(self, fake, *argv):
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(acs_config, "request", fake), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = acs_config.main([*argv, "--dir", str(self.root)])
        return code, out.getvalue(), err.getvalue()

    def read(self, rel):
        return tomllib.loads((self.root / rel).read_text(encoding="utf-8"))


class TomlTests(unittest.TestCase):
    def test_unknown_type_lists_the_types(self):
        with self.assertRaisesRegex(acs_config.ACSConfigError, "unknown type: index. Types: indexes;hec-tokens;"):
            acs_config.select_types("index", acs_config.TYPES)

    def test_writer_rejects_unsupported_values_as_config_errors(self):
        with self.assertRaisesRegex(acs_config.ACSConfigError, "unsupported TOML value"):
            acs_config.dump_toml({"unsupported": 1.5})

    def test_writer_round_trips_objects_and_empty_environments(self):
        obj = {"name": "sample", "enabled": True, "names": ["one", "two"],
               "numbers": [1, 2], "overrides": {"nonprod": {"searchableDays": 30}}}
        dumped = acs_config.dump_toml(obj)
        self.assertTrue(dumped.startswith('name = "sample"\nenabled = true\nnames ='))
        self.assertIn("\n\n[overrides.nonprod]\n", dumped)
        self.assertNotIn("[overrides]\n", dumped)
        self.assertEqual(tomllib.loads(dumped), obj)

        envs = {"nonprod": {}, "prod": {"types": ["roles", "app-permissions"]}}
        dumped = acs_config.dump_toml(envs)
        self.assertIn("[nonprod]", dumped)
        self.assertEqual(tomllib.loads(dumped), envs)

    def test_type_writer_uses_dotted_environment_keys(self):
        dumped = acs_config.dump_toml({"sample": {"itsi.prod": {"foo.bar": 1}}}, dotted=True)
        self.assertIn('"itsi.prod"."foo.bar" = 1', dumped)
        self.assertNotIn('[sample."itsi.prod"]', dumped)
        self.assertEqual(tomllib.loads(dumped), {"sample": {"itsi.prod": {"foo.bar": 1}}})


class EffectiveTests(ACSTestCase):
    def test_layers_apply_in_order(self):
        defaults, repo = acs_config.load_type(self.root, "indexes", acs_config.load_environments(self.root))
        shared, pan = repo["shared"], repo["pan"]
        merged = acs_config.merged
        self.assertEqual(merged("indexes", defaults, shared, "prod")["searchableDays"], 180)
        self.assertEqual(merged("indexes", defaults, shared, "nonprod")["searchableDays"], 60)
        self.assertEqual(merged("indexes", defaults, pan, "nonprod")["searchableDays"], 30)
        self.assertEqual(merged("indexes", defaults, pan, "prod")["searchableDays"], 90)
        self.assertEqual(merged("indexes", defaults, pan, "prod")["datatype"], "event")

    def test_splunk_defaults_are_the_lowest_layer(self):
        self.assertEqual(acs_config.merged("indexes", {}, {"name": "x"}, "prod"),
                         {"name": "x", "datatype": "event", "maxDataSizeMB": 0, "searchableDays": 90})
        self.assertEqual(acs_config.merged("indexes", {"searchableDays": 30}, {"name": "x"}, "prod")["searchableDays"],
                         30)

    def test_default_environment_override_is_scoped(self):
        path = self.root / "objects/app-permissions.toml"
        path.write_text('[default]\nread = ["*"]\n\n[default.nonprod]\nwrite = ["sc_admin"]\n\n[my_app]\n')
        defaults, objects = acs_config.load_type(self.root, "app-permissions", acs_config.load_environments(self.root))
        self.assertEqual(acs_config.merged("app-permissions", defaults, objects["my_app"], "nonprod"),
                         {"name": "my_app", "read": ["*"], "write": ["sc_admin"]})
        self.assertEqual(acs_config.merged("app-permissions", defaults, objects["my_app"], "prod"),
                         {"name": "my_app", "read": ["*"]})

    def test_limits_are_not_pushed_or_deleted_by_default(self):
        self.assertFalse(acs_config.pushed("limits", {}, {}, "prod"))
        self.assertNotIn("delete", acs_config.TYPES["limits"])

    def test_unknown_field_is_an_error(self):
        with self.assertRaisesRegex(acs_config.ACSConfigError, "unknown field"):
            acs_config.merged("indexes", {}, {"name": "x", "bogus": 1}, "prod")


class PullTests(ACSTestCase):
    def test_pull_colors_changed_type_file_in_pipeline(self):
        fake = FakeACS({("GET", "/indexes"): {"indexes": [index("new"), index("pan", searchableDays=200)]}})
        with mock.patch.dict(os.environ, {"TF_BUILD": "True"}):
            code, out, _ = self.run_cli(
                fake, "pull", "prod", "--types", "indexes", "--names", "new pan retired")
        self.assertEqual(code, 0)
        self.assertIn("\033[33mchanged objects/indexes.toml\033[0m", out)
        self.assertNotIn("retired", self.read("objects/indexes.toml"))

    def test_new_object_keeps_only_differences_from_defaults(self):
        fake = FakeACS({("GET", "/indexes"): {"indexes": [index("newidx")]}})
        code, _, _ = self.run_cli(fake, "pull", "prod", "--types", "indexes", "--names", "newidx")
        self.assertEqual(code, 0)
        self.assertEqual(self.read("objects/indexes.toml")["newidx"], {"environments": ["prod"]})

    def test_changed_value_becomes_override(self):
        fake = FakeACS({("GET", "/indexes"): {"indexes": [index("shared", searchableDays=200)]}})
        self.run_cli(fake, "pull", "prod", "--types", "indexes", "--names", "shared")
        self.assertEqual(self.read("objects/indexes.toml")["shared"], {
            "searchableDays": 200, "nonprod": {"searchableDays": 60}})

    def test_equal_value_removes_override(self):
        fake = FakeACS({("GET", "/indexes"): {"indexes": [index("shared", searchableDays=180)]}})
        self.run_cli(fake, "pull", "nonprod", "--types", "indexes", "--names", "shared")
        self.assertEqual(self.read("objects/indexes.toml")["shared"], {"searchableDays": 180})

    def test_field_missing_live_is_unset_for_that_env(self):
        live = {k: v for k, v in index("shared").items() if k != "searchableDays"}
        fake = FakeACS({("GET", "/indexes"): {"indexes": [live]}})
        code, _, _ = self.run_cli(fake, "pull", "nonprod", "--types", "indexes", "--names", "shared")
        self.assertEqual(code, 0)
        self.assertEqual(self.read("objects/indexes.toml")["shared"],
                         {"searchableDays": 180, "nonprod": {"unset": ["searchableDays"]}})
        _, out, _ = self.run_cli(fake, "plan", "nonprod", "--types", "indexes", "--names", "shared")
        self.assertIn("NO DIFFERENCES", out)

    def test_new_live_object_adds_one_stanza_to_existing_file(self):
        envs = acs_config.load_environments(self.root)
        before_defaults, before = acs_config.load_type(self.root, "indexes", envs)
        live = [index("legacy"), index("pan"), index("retired"), index("shared", searchableDays=180),
                index("newidx")]
        fake = FakeACS({("GET", "/indexes"): {"indexes": live}})
        code, _, _ = self.run_cli(fake, "pull", "prod", "--types", "indexes")
        self.assertEqual(code, 0)
        after_defaults, after = acs_config.load_type(self.root, "indexes", envs)
        self.assertEqual(after["newidx"], {"environments": ["prod"], "name": "newidx"})
        self.assertEqual(after_defaults, before_defaults)
        self.assertEqual(set(after) - {"newidx"}, set(before))
        for name, raw in before.items():
            for env in envs:
                self.assertEqual(acs_config.merged("indexes", before_defaults, raw, env),
                                 acs_config.merged("indexes", after_defaults, after[name], env))

    def test_missing_live_drops_env_and_expands_absent_list(self):
        fake = FakeACS({("GET", "/indexes"): {"indexes": []}})
        self.run_cli(fake, "pull", "prod", "--types", "indexes")
        self.assertEqual(self.read("objects/indexes.toml")["legacy"]["environments"], ["nonprod"])
        self.assertNotIn("retired", self.read("objects/indexes.toml"))

    def test_hec_token_is_never_written(self):
        spec = {"name": "newhec", "disabled": False, "useAck": False,
                "defaultIndex": "shared", "token": "SECRET-VALUE"}
        fake = FakeACS({("GET", "/inputs/http-event-collectors"):
                        {"http-event-collectors": [{"spec": spec, "token": "SECRET-VALUE"}]}})
        code, out, err = self.run_cli(fake, "pull", "prod", "--types", "hec-tokens", "--names", "newhec")
        self.assertEqual(code, 0)
        self.assertEqual(self.read("objects/hec-tokens.toml")["newhec"],
                         {"environments": ["prod"], "defaultIndex": "shared"})
        self.assertNotIn("SECRET-VALUE", out + err)
        for path in self.root.rglob("*.toml"):
            self.assertNotIn("SECRET-VALUE", path.read_text(encoding="utf-8"))

    def test_app_permissions_pull(self):
        fake = FakeACS({("GET", "/permissions/apps"):
                        {"apps": [{"name": "my_app", "perms": {"read": ["*"], "write": ["sc_admin"]}}]}})
        code, _, _ = self.run_cli(fake, "pull", "prod", "--types", "app-permissions", "--names", "my_app")
        self.assertEqual(code, 0)
        self.assertEqual(self.read("objects/app-permissions.toml")["my_app"],
                         {"environments": ["prod"], "read": ["*"], "write": ["sc_admin"]})

    def test_app_permissions_pull_keeps_owner(self):
        (self.root / "objects/app-permissions.toml").write_text(
            '[my_app]\nowner = "team"\nread = ["user"]\nwrite = ["user"]\n')
        fake = FakeACS({("GET", "/permissions/apps"):
                        {"apps": [{"name": "my_app", "perms": {"read": ["*"], "write": ["sc_admin"]}}]}})
        code, _, err = self.run_cli(fake, "pull", "prod", "--types", "app-permissions", "--names", "my_app")
        self.assertEqual(code, 0, err)
        defaults, objects = acs_config.load_type(
            self.root, "app-permissions", acs_config.load_environments(self.root))
        self.assertEqual(acs_config.merged("app-permissions", defaults, objects["my_app"], "prod"),
                         {"name": "my_app", "owner": "team", "read": ["*"], "write": ["sc_admin"]})

    def test_splunkbase_apps_pull_keeps_license(self):
        (self.root / "objects/splunkbase-apps.toml").write_text(
            '[my_app]\nid = "old-id"\nversion = "0.9"\nlicense = "my-license"\n\n'
            '[hand_set]\nid = "hand-set-id"\nversion = "0.9"\nlicense = "hand-set-license"\n')
        fake = FakeACS({("GET", "/apps/victoria"): {"apps": [
            {"name": "my_app", "splunkbaseID": "1234", "version": "1.0"},
            {"name": "hand_set", "version": "1.0"},
        ]}})
        code, _, err = self.run_cli(fake, "pull", "prod", "--types", "splunkbase-apps")
        self.assertEqual(code, 0, err)
        defaults, objects = acs_config.load_type(
            self.root, "splunkbase-apps", acs_config.load_environments(self.root))
        self.assertEqual(acs_config.merged("splunkbase-apps", defaults, objects["my_app"], "prod"),
                         {"name": "my_app", "id": "1234", "version": "1.0", "license": "my-license"})
        self.assertEqual(acs_config.merged("splunkbase-apps", defaults, objects["hand_set"], "prod"),
                         {"name": "hand_set", "version": "1.0", "license": "hand-set-license"})

    def test_private_apps_pull_normalizes_name_and_version(self):
        fake = FakeACS({("GET", "/apps/victoria"): {"apps": [
            {"name": "private_app", "version": "1.2.3"},
        ]}})
        code, _, err = self.run_cli(fake, "pull", "prod", "--types", "private-apps")
        self.assertEqual(code, 0, err)
        defaults, objects = acs_config.load_type(
            self.root, "private-apps", acs_config.load_environments(self.root))
        self.assertEqual(acs_config.merged("private-apps", defaults, objects["private_app"], "prod"),
                         {"name": "private_app", "version": "1.2.3"})

    def test_limits_pull_keeps_only_nondefault_settings(self):
        (self.root / "objects/limits.toml").write_text('[default]\nmax_count = "10"\n')
        fake = FakeACS({("GET", "/limits"): [
            {"Stanza": "search", "Values": {"max_count": "10", "max_result_rows": "20"}}]})
        code, _, err = self.run_cli(fake, "pull", "prod", "--types", "limits", "--names", "search")
        self.assertEqual(code, 0, err)
        self.assertEqual(self.read("objects/limits.toml")["search"], {
            "environments": ["prod"], "max_result_rows": "20"})

    def test_built_in_roles_are_skipped_and_imported_roles_mapped(self):
        fake = FakeACS({("GET", "/roles"): {"roles": [
            {"name": "admin", "capabilities": ["admin_all_objects"]},
            {"name": "pan_analyst", "imported": {"roles": ["user"]}, "srchIndexesAllowed": ["pan"],
             "srchDiskQuota": 100, "srchJobsQuota": 3, "rtSrchJobsQuota": 6},
        ]}})
        self.run_cli(fake, "pull", "prod", "--types", "roles", "--names", "admin pan_analyst")
        self.assertNotIn("admin", self.read("objects/roles.toml"))
        self.assertEqual(self.read("objects/roles.toml")["pan_analyst"], {
            "environments": ["prod"], "importedRoles": ["user"], "srchIndexesAllowed": ["pan"]})


class PlanTests(ACSTestCase):
    def test_limits_plan_shows_changed_setting_when_enabled(self):
        (self.root / "objects/limits.toml").write_text('[search]\npush = true\nmax_count = "20"\n')
        fake = FakeACS({("GET", "/limits"): [
            {"Stanza": "search", "Values": {"max_count": "10"}}]})
        code, out, err = self.run_cli(fake, "plan", "prod", "--types", "limits")
        self.assertEqual(code, 0, err)
        self.assertIn('UPDATE limits/search max_count: "10" -> "20"', out)

    def test_app_permissions_push_by_default_uses_inherited_read(self):
        path = self.root / "objects/app-permissions.toml"
        path.write_text('[default]\nread = ["*"]\n\n[my_app]\nwrite = ["sc_admin"]\n')
        fake = FakeACS({("GET", "/permissions/apps"): {
            "apps": [{"name": "my_app", "perms": {"read": ["user"], "write": ["sc_admin"]}}]}})
        code, out, _ = self.run_cli(fake, "plan", "prod", "--types", "app-permissions")
        self.assertEqual(code, 0)
        self.assertIn('UPDATE app-permissions/my_app read: ["user"] -> ["*"]', out)
        self.assertEqual([call[0] for call in fake.calls], ["GET"])

    def test_splunkbase_app_plan_compares_only_version(self):
        (self.root / "objects/splunkbase-apps.toml").write_text(
            '[my_app]\nid = "repo-id"\nversion = "1.1"\nlicense = "my-license"\n')
        fake = FakeACS({("GET", "/apps/victoria"): {"apps": [
            {"name": "my_app", "splunkbaseID": "live-id", "version": "1.0"},
        ]}})
        code, out, err = self.run_cli(fake, "plan", "prod", "--types", "splunkbase-apps")
        self.assertEqual(code, 0, err)
        self.assertIn('UPDATE splunkbase-apps/my_app version: "1.0" -> "1.1"', out)
        self.assertNotIn("repo-id", out)
        self.assertNotIn("license", out)

    def test_types_without_push_are_not_read(self):
        code, out, _ = self.run_cli(FakeACS(), "plan", "prod", "--types", "roles")
        self.assertEqual(code, 0)
        self.assertEqual(out.splitlines()[-1], "NO DIFFERENCES")

    def test_semicolon_separated_types_select_both(self):
        (self.root / "objects/roles.toml").write_text("[analyst]\npush = true\n", encoding="utf-8")
        fake = FakeACS({("GET", "/indexes"): {"indexes": []},
                        ("GET", "/roles"): {"roles": []}})
        code, _, err = self.run_cli(fake, "plan", "prod", "--types", "indexes;roles")
        self.assertEqual(code, 0, err)
        self.assertEqual({call[1] for call in fake.calls if call[0] == "GET"}, {"/indexes", "/roles"})

    def test_object_push_flag_overrides_type_default(self):
        (self.root / "objects/roles.toml").write_text('[analyst]\npush = true\n')
        indexes = self.root / "objects/indexes.toml"
        indexes.write_text(indexes.read_text().replace("[shared]\n", "[shared]\npush = false\n"))
        fake = FakeACS({("GET", "/roles"): {"roles": []},
                        ("GET", "/indexes"): {"indexes": [index("shared", searchableDays=170)]}})
        code, out, _ = self.run_cli(fake, "plan", "prod", "--types", "indexes roles",
                                    "--names", "shared analyst")
        self.assertEqual(code, 0)
        self.assertIn("CREATE roles/analyst", out)
        self.assertNotIn("indexes/shared", out)

    def test_plan_prints_one_line_per_change(self):
        fake = FakeACS({("GET", "/indexes"): {"indexes": [
            index("shared", searchableDays=170), index("pan"), index("extra")]}})
        code, out, _ = self.run_cli(fake, "plan", "prod", "--types", "indexes",
                                    "--names", "shared;pan;extra")
        self.assertEqual(code, 0)
        self.assertEqual(out.splitlines(), [
            "indexes (repo vs prod live)",
            "ONLY LIVE indexes/extra",
            "UPDATE indexes/shared searchableDays: 170 -> 180",
            "2 change(s)",
        ])
        self.assertEqual(fake.writes(), [])

    def test_no_differences(self):
        fake = FakeACS({("GET", "/indexes"): {"indexes": [index("shared", searchableDays=180), index("pan")]}})
        _, out, _ = self.run_cli(fake, "plan", "prod", "--types", "indexes", "--names", "shared pan")
        self.assertIn("NO DIFFERENCES", out.splitlines())

    def test_plan_check_fails_on_differences(self):
        fake = FakeACS({("GET", "/indexes"): {"indexes": [index("shared", searchableDays=170)]}})
        code, out, err = self.run_cli(fake, "plan", "prod", "--types", "indexes",
                                      "--names", "shared", "--check")
        self.assertEqual(code, 1, err)
        self.assertIn("1 change(s)", out)

    def test_plan_check_passes_without_differences(self):
        fake = FakeACS({("GET", "/indexes"): {"indexes": [index("shared", searchableDays=180)]}})
        code, out, err = self.run_cli(fake, "plan", "prod", "--types", "indexes",
                                      "--names", "shared", "--check")
        self.assertEqual(code, 0, err)
        self.assertIn("NO DIFFERENCES", out)


class PushTests(ACSTestCase):
    def test_splunkbase_push_logs_in_once_and_sends_form_headers(self):
        (self.root / "objects/splunkbase-apps.toml").write_text(
            '[new_app]\nid = "1234"\nversion = "1.0"\nlicense = "new-license"\n\n'
            '[existing_app]\nid = "5678"\nversion = "1.1"\nlicense = "existing-license"\n\n'
            '[unlicensed_app]\nid = "9012"\nversion = "1.0"\n')
        requests, reads = [], [0]

        def response(body):
            result = mock.MagicMock()
            result.__enter__.return_value.status = 200
            result.__enter__.return_value.read.return_value = body
            return result

        def open_url(req, timeout):
            requests.append(req)
            if "splunkbase.splunk.com" in req.full_url:
                return response(b"<session><id>session-id</id></session>")
            if req.get_method() == "GET":
                reads[0] += 1
                body = (b'{"apps":[{"name":"existing_app","splunkbaseID":"5678","version":"1.0"}]}'
                        if reads[0] == 1 else
                        b'{"apps":[{"name":"existing_app","splunkbaseID":"5678","version":"1.1"},'
                        b'{"name":"new_app","splunkbaseID":"1234","version":"1.0"},'
                        b'{"name":"unlicensed_app","splunkbaseID":"9012","version":"1.0"}]}')
                return response(body)
            return response(b"{}")

        out, err = io.StringIO(), io.StringIO()
        with mock.patch.dict(os.environ, {
            "SPLUNKBASE_USERNAME": "user", "SPLUNKBASE_PASSWORD": "password"}), \
                mock.patch.object(acs_config, "urlopen", side_effect=open_url), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = acs_config.main([
                "push", "prod", "--types", "splunkbase-apps", "--dir", str(self.root)])
        self.assertEqual(code, 0, err.getvalue())
        login = [req for req in requests if "splunkbase.splunk.com" in req.full_url]
        self.assertEqual(len(login), 1)
        self.assertEqual(login[0].data, b"username=user&password=password")
        installs = [req for req in requests
                    if req.get_method() == "POST" and "admin.splunk.com" in req.full_url]
        updates = [req for req in requests
                   if req.get_method() == "PATCH" and "admin.splunk.com" in req.full_url]
        install = next(req for req in installs if req.data == b"splunkbaseID=1234&version=1.0")
        self.assertEqual(updates[0].data, b"version=1.1")
        for req, license_url in ((install, "new-license"), (updates[0], "existing-license")):
            headers = {key.lower(): value for key, value in req.header_items()}
            self.assertEqual(headers["content-type"], "application/x-www-form-urlencoded")
            self.assertEqual(headers["x-splunkbase-authorization"], "session-id")
            self.assertEqual(headers["acs-licensing-ack"], license_url)
        unlicensed = next(req for req in installs if req.data == b"splunkbaseID=9012&version=1.0")
        headers = {key.lower(): value for key, value in unlicensed.header_items()}
        self.assertNotIn("acs-licensing-ack", headers)

    def test_limits_push_posts_settings(self):
        (self.root / "objects/limits.toml").write_text('[search]\npush = true\nmax_count = "20"\n')
        before = [{"Stanza": "search", "Values": {"max_count": "10"}}]
        after = [{"Stanza": "search", "Values": {"max_count": "20"}}]
        fake = FakeACS({("GET", "/limits"): Seq(before, after)})
        code, _, err = self.run_cli(fake, "push", "prod", "--types", "limits")
        self.assertEqual(code, 0, err)
        self.assertEqual(fake.writes(), [
            ("POST", "/limits/search", {"settings": {"max_count": "20"}})])

    def test_app_permission_patch_contains_only_read_and_write(self):
        before = {"apps": [{"name": "my_app", "perms": {"read": ["user"], "write": ["user"]}}]}
        after = {"apps": [{"name": "my_app", "perms": {"read": ["*"], "write": ["sc_admin"]}}]}
        (self.root / "objects/app-permissions.toml").write_text(
            '[my_app]\nread = ["*"]\nwrite = ["sc_admin"]\n')
        fake = FakeACS({("GET", "/permissions/apps"): Seq(before, after)})
        code, _, err = self.run_cli(fake, "push", "prod", "--types", "app-permissions")
        self.assertEqual(code, 0, err)
        self.assertEqual(fake.writes(), [
            ("PATCH", "/permissions/apps/my_app", {"read": ["*"], "write": ["sc_admin"]})])

    def test_create_and_patch_bodies(self):
        before = {"indexes": [index("shared", searchableDays=170)]}
        after = {"indexes": [index("shared", searchableDays=180), index("pan")]}
        fake = FakeACS({("GET", "/indexes"): Seq(before, after)})
        code, out, _ = self.run_cli(fake, "push", "prod", "--types", "indexes", "--names", "shared pan")
        self.assertEqual(code, 0, out)
        self.assertEqual(fake.writes(), [
            ("POST", "/indexes", {"name": "pan", "datatype": "event", "maxDataSizeMB": 0,
                                  "searchableDays": 90}),
            ("PATCH", "/indexes/shared", {"searchableDays": 180}),
        ])
        self.assertIn("NO DIFFERENCES after push", out)

    def test_202_is_polled_until_the_object_matches(self):
        before = {"indexes": [index("shared", searchableDays=170), index("pan")]}
        after = {"indexes": [index("shared", searchableDays=180), index("pan")]}
        fake = FakeACS({("GET", "/indexes"): Seq(before, before, after)},
                       status={("PATCH", "/indexes/shared"): 202})
        with mock.patch.object(acs_config.time, "sleep") as sleep:
            code, _, _ = self.run_cli(fake, "push", "prod", "--types", "indexes", "--names", "shared pan")
        self.assertEqual(code, 0)
        sleep.assert_called_once_with(10)
        self.assertEqual([c[0] for c in fake.writes()], ["PATCH"])

    def test_extra_object_is_kept_without_delete_and_fails_the_check(self):
        live = {"indexes": [index("shared", searchableDays=180), index("pan"), index("extra")]}
        fake = FakeACS({("GET", "/indexes"): live})
        code, out, err = self.run_cli(fake, "push", "prod", "--types", "indexes",
                                      "--names", "shared pan extra")
        self.assertEqual(code, 1)
        self.assertEqual(fake.writes(), [])
        self.assertEqual(err.count("\n"), 1)
        self.assertIn("1 differences remain after push", err)

    def test_delete_flag_deletes_extra_index_with_data_loss_line(self):
        before = {"indexes": [index("shared", searchableDays=180), index("pan"), index("extra")]}
        after = {"indexes": [index("shared", searchableDays=180), index("pan")]}
        fake = FakeACS({("GET", "/indexes"): Seq(before, after)})
        code, out, _ = self.run_cli(fake, "push", "prod", "--types", "indexes",
                                    "--names", "shared pan extra", "--delete")
        self.assertEqual(code, 0, out)
        self.assertEqual(fake.writes(), [("DELETE", "/indexes/extra", None)])
        self.assertIn("DATA LOSS: deleting index extra", out)

    def test_subnet_add_is_posted_and_removal_needs_delete(self):
        live = {"subnets": ["192.0.2.0/24", "203.0.113.0/24"]}
        added = {"subnets": ["192.0.2.0/24", "198.51.100.0/24", "203.0.113.0/24"]}
        converged = {"subnets": ["192.0.2.0/24", "198.51.100.0/24"]}
        fake = FakeACS({("GET", "/access/hec/ipallowlists"): Seq(live, added)})
        code, _, err = self.run_cli(fake, "push", "prod", "--types", "ip-allowlists", "--names", "hec")
        self.assertEqual(code, 1)
        self.assertEqual(fake.writes(), [("POST", "/access/hec/ipallowlists",
                                          {"subnets": ["198.51.100.0/24"]})])
        self.assertIn("1 differences remain", err)

        fake = FakeACS({("GET", "/access/hec/ipallowlists"): Seq(live, converged)})
        code, _, _ = self.run_cli(fake, "push", "prod", "--types", "ip-allowlists",
                                  "--names", "hec", "--delete")
        self.assertEqual(code, 0)
        self.assertEqual(fake.writes(), [
            ("POST", "/access/hec/ipallowlists", {"subnets": ["198.51.100.0/24"]}),
            ("DELETE", "/access/hec/ipallowlists", {"subnets": ["203.0.113.0/24"]}),
        ])

    def test_outbound_port_post_body(self):
        fake = FakeACS({("GET", "/access/outbound-ports"): Seq(
            [], [{"port": 8089, "name": "svc", "destinationRanges": ["203.0.113.0/24"]}])})
        code, _, _ = self.run_cli(fake, "push", "prod", "--types", "outbound-ports", "--names", "8089")
        self.assertEqual(code, 0)
        self.assertEqual(fake.writes(), [("POST", "/access/outbound-ports", {
            "outboundPorts": [{"port": 8089, "subnets": ["203.0.113.0/24"]}],
            "reason": "Example reason"})])


class InferenceTests(ACSTestCase):
    def setUp(self):
        super().setUp()
        (self.root / "objects/indexes.toml").unlink()

    def test_most_common_value_ties_break_to_the_smallest_json_text(self):
        live = {"a": {"name": "a", "searchableDays": 60}, "b": {"name": "b", "searchableDays": 30}}
        self.assertEqual(acs_config.common_values("indexes", live)["searchableDays"], 30)

    def test_first_pull_writes_default_from_most_common_values(self):
        live = [index("a", searchableDays=30), index("b", searchableDays=30),
                index("c", searchableDays=30), index("d", searchableDays=30, datatype="metric")]
        fake = FakeACS({("GET", "/indexes"): {"indexes": live}})
        code, _, _ = self.run_cli(fake, "pull", "prod", "--types", "indexes")
        self.assertEqual(code, 0)
        indexes = self.read("objects/indexes.toml")
        self.assertEqual(indexes["default"], {"searchableDays": 30})
        self.assertEqual(indexes["a"], {"environments": ["prod"]})
        self.assertEqual(indexes["d"], {"environments": ["prod"], "datatype": "metric"})

    def test_nonprod_pull_after_prod_writes_nonprod_default_and_keeps_default(self):
        prod = {"indexes": [index("a", searchableDays=180), index("b", searchableDays=180)]}
        nonprod = {"indexes": [index("a", searchableDays=30), index("b", searchableDays=30)]}
        fake = FakeACS({("GET", "/indexes"): Seq(prod, nonprod)})
        self.run_cli(fake, "pull", "prod", "--types", "indexes")
        code, _, _ = self.run_cli(fake, "pull", "nonprod", "--types", "indexes")
        self.assertEqual(code, 0)
        indexes = self.read("objects/indexes.toml")
        self.assertEqual(indexes["default"], {"searchableDays": 180, "nonprod": {"searchableDays": 30}})
        self.assertEqual(indexes["a"], {})

    def test_hand_set_default_is_not_changed_by_pull(self):
        path = self.root / "objects/indexes.toml"
        path.write_text("[default]\nsearchableDays = 120\n", encoding="utf-8")
        fake = FakeACS({("GET", "/indexes"): {"indexes": [index("a", searchableDays=90)]}})
        code, _, _ = self.run_cli(fake, "pull", "prod", "--types", "indexes")
        self.assertEqual(code, 0)
        self.assertEqual(self.read("objects/indexes.toml")["default"],
                         {"searchableDays": 120, "prod": {"searchableDays": 90}})

    def test_plan_after_pull_prints_no_differences(self):
        live = {"indexes": [index("a", searchableDays=30), index("b", searchableDays=30),
                            index("c", searchableDays=30), index("d", searchableDays=30, datatype="metric"),
                            index("e", searchableDays=60, maxDataSizeMB=5)]}
        fake = FakeACS({("GET", "/indexes"): live})
        self.run_cli(fake, "pull", "prod", "--types", "indexes")
        _, out, _ = self.run_cli(fake, "plan", "prod", "--types", "indexes")
        self.assertEqual(out.splitlines()[-1], "NO DIFFERENCES")
        self.run_cli(fake, "pull", "nonprod", "--types", "indexes")
        for env in ("prod", "nonprod"):
            with self.subTest(env=env):
                code, out, _ = self.run_cli(fake, "plan", env, "--types", "indexes")
                self.assertEqual(code, 0)
                self.assertEqual(out.splitlines()[-1], "NO DIFFERENCES")

    def test_absence_counts_for_base_and_environment_default_inference(self):
        prod = {"indexes": [index("a", searchableDays=60), index("b", searchableDays=60),
                            index("rare", searchableDays=60, splunkArchivalRetentionDays=180)]}
        nonprod = {"indexes": [index("a", searchableDays=30), index("b", searchableDays=30),
                               index("rare", searchableDays=30, splunkArchivalRetentionDays=180)]}
        for env, live in (("prod", prod), ("nonprod", nonprod)):
            self.run_cli(FakeACS({("GET", "/indexes"): live}), "pull", env, "--types", "indexes")
            _, out, _ = self.run_cli(FakeACS({("GET", "/indexes"): live}),
                                     "plan", env, "--types", "indexes")
            self.assertEqual(out.splitlines()[-1], "NO DIFFERENCES")
        indexes = self.read("objects/indexes.toml")
        self.assertNotIn("splunkArchivalRetentionDays", indexes["default"])
        self.assertNotIn("splunkArchivalRetentionDays", indexes["default"].get("nonprod", {}))
        for name in ("a", "b"):
            self.assertNotIn("unset", indexes[name])
            self.assertNotIn("unset", indexes[name].get("prod", {}))
            self.assertNotIn("unset", indexes[name].get("nonprod", {}))

    def test_pull_compacts_shared_difference_into_object_base(self):
        (self.root / "objects/indexes.toml").write_text(
            "[default]\nsearchableDays = 30\n\n[shared]\n", encoding="utf-8")
        prod = {"indexes": [index("shared", searchableDays=180)]}
        nonprod = {"indexes": [index("shared", searchableDays=180)]}
        code, _, _ = self.run_cli(FakeACS({("GET", "/indexes"): prod}),
                                  "pull", "prod", "--types", "indexes", "--names", "shared")
        self.assertEqual(code, 0)
        for env, live in (("prod", prod), ("nonprod", {"indexes": [index("shared", searchableDays=30)]})):
            _, out, _ = self.run_cli(FakeACS({("GET", "/indexes"): live}),
                                     "plan", env, "--types", "indexes", "--names", "shared")
            self.assertEqual(out.splitlines()[-1], "NO DIFFERENCES")
        code, _, _ = self.run_cli(FakeACS({("GET", "/indexes"): nonprod}),
                                  "pull", "nonprod", "--types", "indexes", "--names", "shared")
        self.assertEqual(code, 0)
        text = (self.root / "objects/indexes.toml").read_text(encoding="utf-8")
        self.assertIn("[shared]\nsearchableDays = 180", text)
        self.assertNotIn("prod.searchableDays", text)
        self.assertNotIn("nonprod.searchableDays", text)
        for env, live in (("prod", prod), ("nonprod", nonprod)):
            _, out, _ = self.run_cli(FakeACS({("GET", "/indexes"): live}),
                                     "plan", env, "--types", "indexes", "--names", "shared")
            self.assertEqual(out.splitlines()[-1], "NO DIFFERENCES")

    def test_nonprod_difference_is_written_inside_object_stanza(self):
        for env, days in (("prod", 90), ("nonprod", 60)):
            fake = FakeACS({("GET", "/indexes"): {"indexes": [index("pan", searchableDays=days)]}})
            code, _, _ = self.run_cli(fake, "pull", env, "--types", "indexes", "--names", "pan")
            self.assertEqual(code, 0)
        text = (self.root / "objects/indexes.toml").read_text(encoding="utf-8")
        self.assertIn("[pan]\nnonprod.searchableDays = 60\n", text)
        self.assertNotIn("[pan.nonprod]", text)
        for env, days in (("nonprod", 60), ("prod", 90)):
            _, out, _ = self.run_cli(
                FakeACS({("GET", "/indexes"): {"indexes": [index("pan", searchableDays=days)]}}),
                "plan", env, "--types", "indexes", "--names", "pan")
            self.assertEqual(out.splitlines()[-1], "NO DIFFERENCES")

    def test_tie_writes_the_first_pulled_env_value_as_the_base(self):
        (self.root / "objects/indexes.toml").write_text("[default]\nsearchableDays = 30\n\n[shared]\n",
                                                         encoding="utf-8")
        for env, days in (("prod", 90), ("nonprod", 60)):
            fake = FakeACS({("GET", "/indexes"): {"indexes": [index("shared", searchableDays=days)]}})
            code, _, _ = self.run_cli(fake, "pull", env, "--types", "indexes", "--names", "shared")
            self.assertEqual(code, 0)
        self.assertEqual(self.read("objects/indexes.toml")["shared"],
                         {"searchableDays": 90, "nonprod": {"searchableDays": 60}})

    def test_missing_defaulted_field_in_both_environments_uses_base_unset(self):
        (self.root / "objects/indexes.toml").write_text(
            "[default]\nsearchableDays = 30\n\n[shared]\n"
            "\n[shared.prod]\nunset = [\"searchableDays\"]\n"
            "\n[shared.nonprod]\nunset = [\"searchableDays\"]\n", encoding="utf-8")
        live = {"indexes": [{k: v for k, v in index("shared").items() if k != "searchableDays"}]}
        for env in ("prod", "nonprod"):
            code, _, _ = self.run_cli(FakeACS({("GET", "/indexes"): live}),
                                      "pull", env, "--types", "indexes", "--names", "shared")
            self.assertEqual(code, 0)
        raw = self.read("objects/indexes.toml")["shared"]
        self.assertEqual(raw["unset"], ["searchableDays"])
        self.assertNotIn("prod", raw)
        self.assertNotIn("nonprod", raw)
        for env in ("prod", "nonprod"):
            _, out, _ = self.run_cli(FakeACS({("GET", "/indexes"): live}),
                                     "plan", env, "--types", "indexes", "--names", "shared")
            self.assertEqual(out.splitlines()[-1], "NO DIFFERENCES")

    def test_old_environment_subtables_still_load_and_plan(self):
        (self.root / "objects/indexes.toml").write_text(
            "[default]\nsearchableDays = 30\n\n[shared]\nsearchableDays = 180\n"
            "\n[shared.nonprod]\nsearchableDays = 60\n", encoding="utf-8")
        for env, days in (("prod", 180), ("nonprod", 60)):
            _, out, _ = self.run_cli(
                FakeACS({("GET", "/indexes"): {"indexes": [index("shared", searchableDays=days)]}}),
                "plan", env, "--types", "indexes", "--names", "shared")
            self.assertEqual(out.splitlines()[-1], "NO DIFFERENCES")


class CopyTests(ACSTestCase):
    def test_copy_prod_to_nonprod_edits_files_only(self):
        code, out, _ = self.run_cli(FakeACS(), "copy", "prod", "nonprod", "--types", "indexes")
        self.assertEqual(code, 0)
        indexes = self.read("objects/indexes.toml")
        self.assertEqual(indexes["shared"], {"searchableDays": 180})
        self.assertEqual(indexes["retired"]["environments"], ["prod", "nonprod"])
        self.assertNotIn("nonprod", indexes["default"])
        self.assertIn("changed objects/indexes.toml", out)


class DocTests(ACSTestCase):
    def test_doc_lists_counts_pushed_types_and_defaults_without_objects(self):
        code, _, _ = self.run_cli(FakeACS(), "doc")
        self.assertEqual(code, 0)
        readme = (self.root / "README.md").read_text(encoding="utf-8")
        self.assertIn("| indexes | `objects/indexes.toml` | yes | 3 | 4 |", readme)
        self.assertIn("| hec-tokens | `objects/hec-tokens.toml` | yes | 1 | 1 |", readme)
        self.assertIn("| roles | `objects/roles.toml` | no | 0 | 0 |", readme)
        self.assertIn("- datatype: event (Splunk default)", readme)
        self.assertIn("- searchableDays: 30 (nonprod, [default])", readme)
        self.assertNotIn("| shared |", readme)

    def test_doc_writes_apps_csv_rows(self):
        (self.root / "objects/app-permissions.toml").write_text(
            '[default]\nread = ["cap-a", "cap-b"]\nwrite = ["sc_admin"]\n\n'
            '[sample_app]\nowner = "owner"\n', encoding="utf-8")
        code, _, _ = self.run_cli(FakeACS(), "doc")
        self.assertEqual(code, 0)
        with (self.root / "apps.csv").open(newline="", encoding="utf-8") as file:
            rows = list(csv.reader(file))
        self.assertEqual(rows, [
            ["env", "app", "version", "read", "write", "owner"],
            ["nonprod", "sample_app", "", "cap-a;cap-b", "sc_admin", "owner"],
            ["prod", "sample_app", "", "cap-a;cap-b", "sc_admin", "owner"],
        ])


class CLITests(ACSTestCase):
    def test_malformed_toml_is_one_error_line_with_file_name(self):
        path = self.root / "objects/indexes.toml"
        path.write_text("[pan\n", encoding="utf-8")
        code, _, err = self.run_cli(FakeACS(), "plan", "prod", "--types", "indexes")
        self.assertEqual(code, 1)
        self.assertEqual(err.count("\n"), 1)
        self.assertIn(str(path), err)
        self.assertNotIn("Traceback", err)

    def test_http_error_is_one_line_without_traceback(self):
        body = io.BytesIO(b'{"code": "forbidden", "message": "not allowed"}')
        error = HTTPError("https://example.invalid", 403, "Forbidden", {}, body)
        with mock.patch.object(acs_config, "urlopen", side_effect=error):
            code, _, err = self.run_cli(acs_config.request, "plan", "prod", "--types", "indexes")
        self.assertEqual(code, 1)
        self.assertEqual(err.count("\n"), 1)
        self.assertIn("HTTP 403 GET https://admin.splunk.com/stack/adminconfig/v2/indexes", err)
        self.assertIn("not allowed", err)
        self.assertNotIn("Traceback", err)

    def test_invalid_api_json_is_one_error_line_without_traceback(self):
        response = mock.MagicMock()
        response.status = 200
        response.read.return_value = b"not JSON"
        response.__enter__.return_value = response
        with mock.patch.object(acs_config, "urlopen", return_value=response):
            code, _, err = self.run_cli(acs_config.request, "plan", "prod", "--types", "indexes")
        self.assertEqual(code, 1)
        self.assertEqual(err.count("\n"), 1)
        self.assertIn("invalid JSON from GET", err)
        self.assertNotIn("Traceback", err)

    def test_invalid_api_utf8_is_one_error_line_without_traceback(self):
        response = mock.MagicMock()
        response.status = 200
        response.read.return_value = b"\xff"
        response.__enter__.return_value = response
        with mock.patch.object(acs_config, "urlopen", return_value=response):
            code, _, err = self.run_cli(acs_config.request, "plan", "prod", "--types", "indexes")
        self.assertEqual(code, 1)
        self.assertEqual(err.count("\n"), 1)
        self.assertIn("invalid UTF-8 response from GET", err)
        self.assertNotIn("Traceback", err)

    def test_unknown_environment_table_is_one_error_line(self):
        path = self.root / "objects/indexes.toml"
        path.write_text(path.read_text(encoding="utf-8") + "\n[pan.staging]\nsearchableDays = 1\n", encoding="utf-8")
        code, _, err = self.run_cli(FakeACS(), "plan", "prod", "--types", "indexes")
        self.assertEqual(code, 1)
        self.assertEqual(err.count("\n"), 1)
        self.assertIn(f"{path}: unknown environment table [pan.staging]", err)
        self.assertNotIn("Traceback", err)

    def test_default_that_is_not_a_table_is_one_error_line(self):
        path = self.root / "objects/indexes.toml"
        path.write_text('default = "x"\n', encoding="utf-8")
        code, _, err = self.run_cli(FakeACS(), "plan", "prod", "--types", "indexes")
        self.assertEqual(code, 1)
        self.assertEqual(err.count("\n"), 1)
        self.assertIn("[default] must be a table", err)

    def test_live_object_named_default_is_one_error_line(self):
        fake = FakeACS({("GET", "/indexes"): {"indexes": [index("default")]}})
        code, _, err = self.run_cli(fake, "plan", "prod", "--types", "indexes")
        self.assertEqual(code, 1)
        self.assertEqual(err.count("\n"), 1)
        self.assertIn("live object 'default' is reserved", err)

    def test_invalid_utf8_toml_is_one_error_line_without_traceback(self):
        path = self.root / "objects/indexes.toml"
        path.write_bytes(b"\xff")
        code, _, err = self.run_cli(FakeACS(), "plan", "prod", "--types", "indexes")
        self.assertEqual(code, 1)
        self.assertEqual(err.count("\n"), 1)
        self.assertIn(str(path), err)
        self.assertNotIn("Traceback", err)

    def test_missing_stack_variable_is_one_line(self):
        with mock.patch.dict(os.environ, {"STACK_TOKEN": "x"}, clear=True):
            code, _, err = self.run_cli(acs_config.request, "plan", "prod", "--types", "indexes")
        self.assertEqual(code, 1)
        self.assertEqual(err, "ERROR: SPLUNK_STACK is not set\n")


class OutputTests(unittest.TestCase):
    def test_result_colors(self):
        cases = {
            "CREATE indexes/pan": "32",
            "ADD SUBNETS ip-allowlists/hec": "32",
            "NO DIFFERENCES": "32",
            "NO DIFFERENCES after push": "32",
            "UPDATE indexes/pan searchableDays": "33",
            "changed objects/indexes/pan.toml": "33",
            "REMOVE SUBNETS ip-allowlists/hec": "31",
            "DELETE indexes/old": "31",
            "ONLY LIVE indexes/extra": "31",
            "deleted objects/indexes/old.toml": "31",
            "DATA LOSS: deleting index old": "31",
            "ERROR: failed": "31",
            "##[error]failed": "31",
        }
        with mock.patch.dict(os.environ, {"TF_BUILD": "true"}):
            for line, color in cases.items():
                with self.subTest(line=line):
                    self.assertEqual(acs_config.color_line(line), f"\033[{color}m{line}\033[0m")

    def test_colors_require_pipeline_or_terminal(self):
        line = "CREATE indexes/pan"
        stdout = mock.Mock(isatty=mock.Mock(return_value=False))
        with mock.patch.dict(os.environ, {}, clear=True), mock.patch.object(acs_config.sys, "stdout", stdout):
            self.assertEqual(acs_config.color_line(line), line)
            stdout.isatty.return_value = True
            self.assertEqual(acs_config.color_line(line), f"\033[32m{line}\033[0m")

    def test_pipeline_message_prefixes(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(acs_config.pipeline_message("error", "failed"), "ERROR: failed")
            self.assertEqual(acs_config.pipeline_message("warning", "skipped"), "WARNING: skipped")
            self.assertEqual(acs_config.pipeline_message("section", "indexes"), "indexes")
        with mock.patch.dict(os.environ, {"TF_BUILD": "true"}):
            self.assertEqual(acs_config.pipeline_message("error", "failed"), "##[error]failed")
            self.assertEqual(acs_config.pipeline_message("warning", "skipped"), "##[warning]skipped")
            self.assertEqual(acs_config.pipeline_message("section", "indexes"), "##[section]indexes")


if __name__ == "__main__":
    unittest.main()
