"""Tests for pipeline/open_pr.py."""

import io
import json
import os
import subprocess
import tempfile
import unittest
import urllib.error
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import MagicMock, patch

from pipeline import open_pr

ENV = {
    "BUILD_BUILDID": "123",
    "BUILD_REPOSITORY_ID": "repo-id",
    "BUILD_REPOSITORY_NAME": "config",
    "SYSTEM_ACCESSTOKEN": "test-token",
    "SYSTEM_COLLECTIONURI": "https://example.invalid/",
    "SYSTEM_TEAMPROJECT": "project",
    "SYSTEM_TEAMPROJECTID": "project-id",
}


def run(func, *args, status="", remote="", urlopen_effect=None):
    """Run func with git returning `status` for status and `remote` for ls-remote."""
    def fake_git(cmd, **_):
        out = {"status": status, "ls-remote": remote}.get(cmd[5], "")
        return subprocess.CompletedProcess(cmd, 0, stdout=out)

    response = MagicMock()
    response.read.return_value = b'{"pullRequestId": 42}'
    urlopen = MagicMock(side_effect=urlopen_effect)
    urlopen.return_value.__enter__.return_value = response
    out = io.StringIO()
    with (
        patch("pipeline.open_pr.subprocess.run", side_effect=fake_git) as git_run,
        patch("pipeline.open_pr.urllib.request.urlopen", urlopen),
        patch.dict(os.environ, ENV, clear=True),
        redirect_stdout(out),
    ):
        func(*args)
    return [c.args[0][5:] for c in git_run.call_args_list], urlopen, out.getvalue()


class OpenPrTests(unittest.TestCase):
    def test_branch_starts_new(self):
        calls, _, out = run(open_pr.branch)
        self.assertEqual(calls[-1], ["checkout", "-B", "acs-pull/123"])
        self.assertEqual(out, "Starting acs-pull/123\n")

    def test_branch_continues_pushed_branch(self):
        calls, _, _ = run(open_pr.branch, remote="abc\trefs/heads/acs-pull/123\n")
        self.assertIn(["fetch", "origin", "acs-pull/123"], calls)
        self.assertEqual(calls[-1], ["checkout", "-B", "acs-pull/123", "FETCH_HEAD"])

    def test_publish_commits_pushes_and_opens_pull_request(self):
        calls, urlopen, out = run(open_pr.publish, "prod", status=" M objects/indexes/pan.json\n")
        self.assertIn(["commit", "-m", "Pull prod ACS settings"], calls)
        self.assertIn(["push", "origin", "HEAD:refs/heads/acs-pull/123"], calls)
        request = urlopen.call_args.args[0]
        self.assertEqual(
            request.full_url,
            "https://example.invalid/project-id/_apis/git/repositories/repo-id/pullrequests?api-version=7.1",
        )
        self.assertEqual(request.get_header("Authorization"), "Bearer test-token")
        body = json.loads(request.data)
        self.assertEqual(body["sourceRefName"], "refs/heads/acs-pull/123")
        self.assertEqual(body["targetRefName"], "refs/heads/main")
        self.assertEqual(out, "https://example.invalid/project/_git/config/pullrequest/42\n")

    def test_publish_with_open_pull_request(self):
        conflict = urllib.error.HTTPError("u", 409, "Conflict", {}, None)
        _, _, out = run(open_pr.publish, "nonprod", status=" M x\n", urlopen_effect=conflict)
        self.assertEqual(out, "Pull request for acs-pull/123 is already open\n")

    def test_publish_without_changes_or_branch(self):
        calls, urlopen, out = run(open_pr.publish, "prod")
        self.assertNotIn("push", [c[0] for c in calls])
        urlopen.assert_not_called()
        self.assertEqual(out, "NO DIFFERENCES in prod\n")

    def test_changes_lists_objects_by_file(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {}, clear=True):
            git = ["git", "-C", tmp, "-c", "user.name=t", "-c", "user.email=t@localhost"]
            subprocess.run([*git, "init", "-q"], check=True)
            objects = Path(tmp, "objects")
            objects.mkdir()
            (objects / "indexes.toml").write_text('[default]\nsearchableDays = 90\n\n[old]\n\n[pan]\nsearchableDays = 30\n')
            (objects / "roles.toml").write_text("[analyst]\n")
            subprocess.run([*git, "add", "-A"], check=True)
            subprocess.run([*git, "commit", "-qm", "base"], check=True)
            (objects / "indexes.toml").write_text('[default]\nsearchableDays = 90\n\n[new]\nnonprod.searchableDays = 7\n\n'
                                                  '[pan]\nsearchableDays = 60\n')
            out = io.StringIO()
            cwd = os.getcwd()
            try:
                os.chdir(tmp)
                with redirect_stdout(out):
                    open_pr.changes()
            finally:
                os.chdir(cwd)
        self.assertIn("objects/indexes.toml (3 objects)\n"
                      "created [new] 1 fields\ndeleted [old] 0 fields\nchanged [pan] 1 fields\n", out.getvalue())
        self.assertNotIn("roles.toml", out.getvalue())


if __name__ == "__main__":
    unittest.main()
