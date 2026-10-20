"""Unit tests for acs_config.py. ACS is replaced by a fake request function; nothing touches the network."""

import contextlib
import copy
import io
import json
import os
import shutil
import tempfile
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
        return json.loads((self.root / rel).read_text(encoding="utf-8"))


class EffectiveTests(ACSTestCase):
    def test_layers_apply_in_order(self):
        defaults = acs_config.load_defaults(self.root, "indexes")
        repo = acs_config.load_repo(self.root, "indexes")
        shared, pan = repo["shared"][1], repo["pan"][1]
        merged = acs_config.merged
        self.assertEqual(merged("indexes", defaults, shared, "prod")["searchableDays"], 180)
        self.assertEqual(merged("indexes", defaults, shared, "nonprod")["searchableDays"], 60)
        self.assertEqual(merged("indexes", defaults, pan, "nonprod")["searchableDays"], 30)
        self.assertEqual(merged("indexes", defaults, pan, "prod")["searchableDays"], 90)
        self.assertEqual(merged("indexes", defaults, pan, "prod")["datatype"], "event")

    def test_unknown_field_is_an_error(self):
        with self.assertRaisesRegex(acs_config.ACSConfigError, "unknown field"):
            acs_config.merged("indexes", {}, {"name": "x", "bogus": 1}, "prod")


class PullTests(ACSTestCase):
    def test_new_object_keeps_only_differences_from_defaults(self):
        fake = FakeACS({("GET", "/indexes"): {"indexes": [index("newidx")]}})
        code, _, _ = self.run_cli(fake, "pull", "prod", "--types", "indexes", "--names", "newidx")
        self.assertEqual(code, 0)
        self.assertEqual(self.read("objects/indexes/newidx.json"),
                         {"environments": ["prod"], "name": "newidx"})

    def test_changed_value_becomes_override(self):
        fake = FakeACS({("GET", "/indexes"): {"indexes": [index("shared", searchableDays=200)]}})
        self.run_cli(fake, "pull", "prod", "--types", "indexes", "--names", "shared")
        self.assertEqual(self.read("objects/indexes/shared.json"), {
            "name": "shared", "searchableDays": 180,
            "overrides": {"nonprod": {"searchableDays": 60}, "prod": {"searchableDays": 200}}})

    def test_equal_value_removes_override(self):
        fake = FakeACS({("GET", "/indexes"): {"indexes": [index("shared", searchableDays=180)]}})
        self.run_cli(fake, "pull", "nonprod", "--types", "indexes", "--names", "shared")
        self.assertEqual(self.read("objects/indexes/shared.json"),
                         {"name": "shared", "searchableDays": 180})

    def test_missing_live_drops_env_and_expands_absent_list(self):
        fake = FakeACS({("GET", "/indexes"): {"indexes": []}})
        self.run_cli(fake, "pull", "prod", "--types", "indexes")
        self.assertEqual(self.read("objects/indexes/legacy.json")["environments"], ["nonprod"])
        self.assertFalse((self.root / "objects/indexes/retired.json").exists())

    def test_hec_token_is_never_written(self):
        spec = {"name": "newhec", "disabled": False, "useAck": False,
                "defaultIndex": "shared", "token": "SECRET-VALUE"}
        fake = FakeACS({("GET", "/inputs/http-event-collectors"):
                        {"http-event-collectors": [{"spec": spec, "token": "SECRET-VALUE"}]}})
        code, out, err = self.run_cli(fake, "pull", "prod", "--types", "hec-tokens", "--names", "newhec")
        self.assertEqual(code, 0)
        self.assertEqual(self.read("objects/hec-tokens/newhec.json"),
                         {"defaultIndex": "shared", "environments": ["prod"], "name": "newhec"})
        self.assertNotIn("SECRET-VALUE", out + err)
        for path in self.root.rglob("*.json"):
            self.assertNotIn("SECRET-VALUE", path.read_text(encoding="utf-8"))

    def test_built_in_roles_are_skipped_and_imported_roles_mapped(self):
        fake = FakeACS({("GET", "/roles"): {"roles": [
            {"name": "admin", "capabilities": ["admin_all_objects"]},
            {"name": "pan_analyst", "imported": {"roles": ["user"]}, "srchIndexesAllowed": ["pan"]},
        ]}})
        self.run_cli(fake, "pull", "prod", "--types", "roles")
        self.assertFalse((self.root / "objects/roles/admin.json").exists())
        self.assertEqual(self.read("objects/roles/pan_analyst.json"), {
            "environments": ["prod"], "importedRoles": ["user"], "name": "pan_analyst",
            "srchIndexesAllowed": ["pan"]})


class PlanTests(ACSTestCase):
    def test_plan_prints_one_line_per_change(self):
        fake = FakeACS({("GET", "/indexes"): {"indexes": [
            index("shared", searchableDays=170), index("pan"), index("extra")]}})
        code, out, _ = self.run_cli(fake, "plan", "prod", "--types", "indexes",
                                    "--names", "shared pan extra")
        self.assertEqual(code, 0)
        self.assertEqual(out.splitlines(), [
            "indexes",
            "ONLY LIVE indexes/extra",
            "UPDATE indexes/shared searchableDays: 170 -> 180",
            "2 change(s)",
        ])
        self.assertEqual(fake.writes(), [])

    def test_no_differences(self):
        fake = FakeACS({("GET", "/indexes"): {"indexes": [index("shared", searchableDays=180), index("pan")]}})
        _, out, _ = self.run_cli(fake, "plan", "prod", "--types", "indexes", "--names", "shared pan")
        self.assertIn("NO DIFFERENCES", out.splitlines())


class PushTests(ACSTestCase):
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


class CopyTests(ACSTestCase):
    def test_copy_prod_to_nonprod_edits_files_only(self):
        code, out, _ = self.run_cli(FakeACS(), "copy", "prod", "nonprod", "--types", "indexes")
        self.assertEqual(code, 0)
        self.assertEqual(self.read("objects/indexes/shared.json"), {"name": "shared", "searchableDays": 180})
        self.assertEqual(self.read("objects/indexes/retired.json")["environments"], ["prod", "nonprod"])
        self.assertNotIn("overrides", self.read("objects/indexes/_defaults.json"))
        self.assertIn("changed objects/indexes/retired.json", out)


class DocTests(ACSTestCase):
    def test_doc_bolds_values_that_differ_between_envs(self):
        code, _, _ = self.run_cli(FakeACS(), "doc")
        self.assertEqual(code, 0)
        readme = (self.root / "README.md").read_text(encoding="utf-8")
        self.assertIn("| shared | searchableDays | **60** | **180** |", readme)
        self.assertIn("| pan | searchableDays | **30** | **90** |", readme)
        self.assertIn("| pan | datatype | event | event |", readme)


class CLITests(ACSTestCase):
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

    def test_missing_stack_variable_is_one_line(self):
        with mock.patch.dict(os.environ, {"STACK_TOKEN": "x"}, clear=True):
            code, _, err = self.run_cli(acs_config.request, "plan", "prod", "--types", "indexes")
        self.assertEqual(code, 1)
        self.assertEqual(err, "ERROR: SPLUNK_STACK is not set\n")


if __name__ == "__main__":
    unittest.main()
