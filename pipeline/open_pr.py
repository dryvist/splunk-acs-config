"""Share one pull branch across a run's pull jobs and open its Azure Repos pull request.

open_pr.py branch          check out acs-pull/<build id>, continuing it when an earlier job pushed it
open_pr.py changes         print the objects this job's pull created, changed or deleted, grouped by file
open_pr.py publish <env>   commit the pulled <env> settings, push the branch, and open the pull request once
"""

import json
import os
import subprocess
import sys
import tomllib
import urllib.error
import urllib.request
from pathlib import Path

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


def flat(table, prefix=""):
    """Map dotted field names, including environment overrides, to values."""
    out = {}
    for key, value in table.items():
        out.update(flat(value, f"{prefix}{key}.") if isinstance(value, dict) else {f"{prefix}{key}": value})
    return out


def changes():
    tracked = set(git("ls-tree", "--name-only", "HEAD", "objects/").split())
    paths = sorted(tracked | {p.as_posix() for p in Path("objects").glob("*.toml")})
    shown = 0
    for path in paths:
        old = tomllib.loads(git("show", f"HEAD:{path}")) if path in tracked else {}
        new = tomllib.loads(Path(path).read_text(encoding="utf-8")) if Path(path).exists() else {}
        lines = []
        for name in sorted(old.keys() | new.keys()):
            a, b = flat(old.get(name, {})), flat(new.get(name, {}))
            if name in old and name in new and a == b:
                continue
            status = "created" if name not in old else "deleted" if name not in new else "changed"
            lines.append(f"{status} [{name}] {sum(a.get(k) != b.get(k) for k in a.keys() | b.keys())} fields")
        if lines:
            shown += 1
            print(pipeline_message("section", "=" * 100))
            print(pipeline_message("group", f"{path} ({len(lines)} objects)"))
            for line in lines:
                print(color_line(line))
            if "TF_BUILD" in os.environ:
                print("##[endgroup]")
    if not shown:
        print(color_line("NO DIFFERENCES"))


def fail(message):
    sys.exit(color_line(pipeline_message("error", message)))


if __name__ == "__main__":
    try:
        if sys.argv[1:2] == ["branch"]:
            branch()
        elif sys.argv[1:2] == ["changes"]:
            changes()
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
