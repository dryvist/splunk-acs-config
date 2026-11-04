"""Share one pull branch across a run's pull jobs and open its Azure Repos pull request.

open_pr.py branch          check out acs-pull/<build id>, continuing it when an earlier job pushed it
open_pr.py publish <env>   commit the pulled <env> settings, push the branch, and open the pull request once
"""

import json
import os
import subprocess
import sys
import urllib.error
import urllib.request

if __package__:
    from .output import color_line, pipeline_message
else:
    from output import color_line, pipeline_message


def git(*args):
    return subprocess.run(
        ["git", "-c", "user.name=Azure Pipelines", "-c", "user.email=azure-pipelines@localhost", *args],
        check=True, capture_output=True, text=True,
    ).stdout


def branch_name():
    return f"acs-pull/{os.environ['BUILD_BUILDID']}"


def remote_branch_exists():
    return bool(git("ls-remote", "--heads", "origin", branch_name()).strip())


def branch():
    name = branch_name()
    if remote_branch_exists():
        git("fetch", "origin", name)
        git("checkout", "-B", name, "FETCH_HEAD")
        print(f"Continuing {name}")
    else:
        git("checkout", "-B", name)
        print(f"Starting {name}")


def publish(env):
    if git("status", "--porcelain").strip():
        git("add", "--all")
        git("commit", "-m", f"Pull {env} ACS settings")
        git("push", "origin", f"HEAD:refs/heads/{branch_name()}")
    else:
        print(color_line(f"NO DIFFERENCES in {env}"))
        if not remote_branch_exists():
            return
    e = os.environ
    body = {
        "sourceRefName": f"refs/heads/{branch_name()}",
        "targetRefName": "refs/heads/main",
        "title": f"Pull ACS settings (build {e['BUILD_BUILDID']})",
        "description": f"ACS settings pulled by build {e['BUILD_BUILDID']}.",
    }
    request = urllib.request.Request(
        f"{e['SYSTEM_COLLECTIONURI']}{e['SYSTEM_TEAMPROJECTID']}/_apis/git/repositories/"
        f"{e['BUILD_REPOSITORY_ID']}/pullrequests?api-version=7.1",
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {e['SYSTEM_ACCESSTOKEN']}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            pr_id = json.loads(response.read())["pullRequestId"]
    except urllib.error.HTTPError as error:
        if error.code != 409:
            raise
        error.close()
        print(f"Pull request for {branch_name()} is already open")
        return
    print(f"{e['SYSTEM_COLLECTIONURI']}{e['SYSTEM_TEAMPROJECT']}/_git/{e['BUILD_REPOSITORY_NAME']}/pullrequest/{pr_id}")


def fail(message):
    sys.exit(color_line(pipeline_message("error", message)))


if __name__ == "__main__":
    try:
        if sys.argv[1:2] == ["branch"]:
            branch()
        else:
            publish(sys.argv[2])
    except subprocess.CalledProcessError as error:
        fail(f"{' '.join(error.cmd)} exited with code {error.returncode}: {error.stderr.strip()}")
    except urllib.error.HTTPError as error:
        message = f"HTTP {error.code} from {error.url}: {error.read().decode(errors='replace')}"
        error.close()
        fail(message)
    except KeyError as error:
        fail(f"Missing pipeline variable {error}")
