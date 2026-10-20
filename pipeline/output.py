"""Format command output for local use and Azure Pipelines."""

import os
import sys


def color_line(line):
    if "TF_BUILD" not in os.environ and not sys.stdout.isatty():
        return line
    if line.startswith(("CREATE ", "ADD ", "created ", "NO DIFFERENCES")):
        color = "32"
    elif line.startswith(("UPDATE ", "changed ")):
        color = "33"
    elif line.startswith(("REMOVE ", "DELETE ", "ONLY LIVE ", "deleted ", "DATA LOSS:",
                          "ERROR: ", "##[error]")):
        color = "31"
    else:
        return line
    return f"\033[{color}m{line}\033[0m"


def pipeline_message(level, message):
    if "TF_BUILD" in os.environ:
        return f"##[{level}]{message}"
    return message if level in ("section", "group") else f"{level.upper()}: {message}"
