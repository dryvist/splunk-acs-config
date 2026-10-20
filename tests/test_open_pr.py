"""Tests for pipeline/open_pr.py."""

import io
import json
import os
import subprocess
import unittest
from contextlib import redirect_stdout
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


def run(status):
    response = MagicMock()
    response.read.return_value = b'{"pullRequestId": 42}'
    urlopen = MagicMock()
    urlopen.return_value.__enter__.return_value = response
    result = subprocess.CompletedProcess([], 0, stdout=status)
    out = io.StringIO()
    with (
        patch("pipeline.open_pr.subprocess.run", return_value=result) as git_run,
        patch("pipeline.open_pr.urllib.request.urlopen", urlopen),
        patch.dict(os.environ, ENV, clear=True),
        redirect_stdout(out),
    ):
        open_pr.open_pr("nonprod")
    return [c.args[0][5:] for c in git_run.call_args_list], urlopen, out.getvalue()


class OpenPrTests(unittest.TestCase):
    def test_commits_pushes_and_opens_pull_request(self):
        calls, urlopen, out = run(" M objects/indexes/pan.json\n")
        self.assertIn(["checkout", "-b", "acs-pull/nonprod-123"], calls)
        self.assertEqual(calls[-1], ["push", "origin", "HEAD:refs/heads/acs-pull/nonprod-123"])
        request = urlopen.call_args.args[0]
        self.assertEqual(
            request.full_url,
            "https://example.invalid/project-id/_apis/git/repositories/repo-id/pullrequests?api-version=7.1",
        )
        self.assertEqual(request.get_header("Authorization"), "Bearer test-token")
        body = json.loads(request.data)
        self.assertEqual(body["sourceRefName"], "refs/heads/acs-pull/nonprod-123")
        self.assertEqual(body["targetRefName"], "refs/heads/main")
        self.assertEqual(out, "https://example.invalid/project/_git/config/pullrequest/42\n")

    def test_no_changes_skips_push_and_request(self):
        calls, urlopen, out = run("")
        self.assertEqual(calls, [["status", "--porcelain"]])
        urlopen.assert_not_called()
        self.assertEqual(out, "NO DIFFERENCES\n")


if __name__ == "__main__":
    unittest.main()
