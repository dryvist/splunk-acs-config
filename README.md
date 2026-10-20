# Splunk ACS configuration

Store Splunk Cloud ACS settings in TOML files and use `acs_config.py` to pull,
compare, push, copy, and document those settings through the ACS API.

## Repository contents

- `acs_config.py`: command-line tool for ACS settings.
- `pipeline/`: pipeline helpers. `open_pr.py` publishes pulled settings as a
  pull request. `output.py` formats command output.
- `templates/`: reusable Azure Pipelines templates.
- `example/`: sample configuration and pipeline.
- `tests/`: unit tests.
- `wiki/`: setup, reference, and troubleshooting pages.

## Installation

Clone the repository. Run it with Python 3.11 or later. The tool uses only the
standard library, so there is nothing to install.

## Usage

From the repository root, set the stack and token for the example
configuration, then run a read-only plan:

~~~sh
cd example
export SPLUNK_STACK="<stack>"
export ACS_TOKEN="<acs-token>"
python3 ../acs_config.py plan nonprod --dir .
~~~

Set `SPLUNK_SEARCH_HEAD` when the ACS endpoint uses a search head. See
[Commands](wiki/Reference/Commands.md) for filters, other actions, and
environment variables.

## Pipeline

The example pipeline uses the shared template. Pull requests run a read-only
plan. A pull reads the selected environments and opens a pull request for file
changes. Push writes only indexes and HEC tokens, plus any object with
`push = true`. A push runs as a deployment job on environment `splunk-<env>`,
so any approval configured on that environment gates the deployment. Push runs only
when the pipeline is manually queued with action `push`; nothing pushes on a
commit or pull request.

## Wiki

- [Wiki home](wiki/Home.md)
- [Getting started](wiki/Getting-started.md)
- [Reference](wiki/Reference.md)
- [Troubleshooting](wiki/Troubleshooting.md)
