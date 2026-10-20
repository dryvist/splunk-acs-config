# Splunk ACS configuration

Store Splunk Cloud ACS settings in TOML files and use `acs_config.py` to pull,
compare, push, copy, and document those settings through the ACS API.

## Repository contents

- `acs_config.py`: command-line tool for ACS settings.
- `pipeline/open_pr.py`: pipeline helper that publishes pulled settings.
- `templates/`: reusable Azure Pipelines templates.
- `example/`: sample configuration and pipeline.
- `wiki/`: setup, reference, and troubleshooting pages.

## Quick start

From the tools repo, use the sample configuration to set the ACS endpoint and
token, then run a read-only plan:

~~~sh
cd example
export SPLUNK_STACK="<stack>"
export ACS_TOKEN="<acs-token>"
python3 ../acs_config.py plan nonprod --dir .
~~~

Set `SPLUNK_SEARCH_HEAD` when the ACS endpoint uses a search head. See the
Commands page for filters, other actions, and environment variables.

## Pipeline

The example pipeline uses the shared template. Pull requests run a read-only
plan. A pull reads the selected environments and opens a pull request for file
changes. A push runs as a deployment job on environment `splunk-<env>`, so any
approval configured on that environment gates the deployment. Push runs only
when the pipeline is manually queued with action `push`; nothing pushes on a
commit or pull request.

## Wiki

- [Wiki home](wiki/Home.md)
- [Getting started](wiki/Getting-started.md)
- [Reference](wiki/Reference.md)
- [File format](wiki/Reference/File-format.md)
- [Commands](wiki/Reference/Commands.md)
- [Object types](wiki/Reference/Object-types.md)
- [Copy between environments](wiki/Reference/Copy-between-environments.md)
- [Push one object](wiki/Reference/Push-one-object.md)
- [Troubleshooting](wiki/Troubleshooting.md)
