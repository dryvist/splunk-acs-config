"""Commit pulled ACS settings to a new branch and open an Azure Repos pull request."""

import json
import os
import subprocess
import sys
import urllib.error
import urllib.request


def git(*args):
    return subprocess.run(
        ["git", "-c", "user.name=Azure Pipelines", "-c", "user.email=azure-pipelines@localhost", *args],
        check=True, capture_output=True, text=True,
    ).stdout


def open_pr(env):
    if not git("status", "--porcelain").strip():
        print("NO DIFFERENCES")
        return
    e = os.environ
    branch = f"acs-pull/{env}-{e['BUILD_BUILDID']}"
    git("checkout", "-b", branch)
    git("add", "--all")
    git("commit", "-m", f"Pull {env} ACS settings")
    git("push", "origin", f"HEAD:refs/heads/{branch}")
    body = {
        "sourceRefName": f"refs/heads/{branch}",
        "targetRefName": "refs/heads/main",
        "title": f"Pull {env} ACS settings",
        "description": f"ACS settings pulled from {env} by build {e['BUILD_BUILDID']}.",
    }
    request = urllib.request.Request(
        f"{e['SYSTEM_COLLECTIONURI']}{e['SYSTEM_TEAMPROJECTID']}/_apis/git/repositories/"
        f"{e['BUILD_REPOSITORY_ID']}/pullrequests?api-version=7.1",
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {e['SYSTEM_ACCESSTOKEN']}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        pr_id = json.loads(response.read())["pullRequestId"]
    print(f"{e['SYSTEM_COLLECTIONURI']}{e['SYSTEM_TEAMPROJECT']}/_git/{e['BUILD_REPOSITORY_NAME']}/pullrequest/{pr_id}")


if __name__ == "__main__":
    try:
        open_pr(sys.argv[1])
    except subprocess.CalledProcessError as error:
        sys.exit(f"##[error]{' '.join(error.cmd)} exited with code {error.returncode}: {error.stderr.strip()}")
    except urllib.error.HTTPError as error:
        sys.exit(f"##[error]HTTP {error.code} from {error.url}: {error.read().decode(errors='replace')}")
    except KeyError as error:
        sys.exit(f"##[error]Missing pipeline variable {error}")
