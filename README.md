# Splunk ACS configuration

Keep Splunk Cloud ACS settings as JSON files in a private configuration
repository. Use the files as readable documentation, a backup, and a source
for restoring or copying settings between environments.

## Files

**environments.json** lists the environments. The objects directory contains
one JSON file per ACS object and an optional **_defaults.json** for each type.
The **example/** directory contains a sample configuration and pipeline.

The effective object fields are layered in this order:

1. Type defaults.
2. Type default overrides for the selected environment.
3. Object fields.
4. Object overrides for the selected environment.

Each layer replaces whole field values. An object can restrict its
environments with the environments field.

## Ad hoc use

Set SPLUNK_STACK and ACS_TOKEN in the shell. Set SPLUNK_SEARCH_HEAD
when the ACS endpoint is for a search head.

~~~sh
export SPLUNK_STACK="<stack>"
export ACS_TOKEN="<acs-token>"
python3 acs_config.py pull nonprod
python3 acs_config.py plan nonprod
python3 acs_config.py push nonprod
python3 acs_config.py copy nonprod prod
python3 acs_config.py doc
~~~

Use --dir to select another configuration directory. Use --types and
--names to limit a command. push --delete removes live-only objects.

## Pipeline

The example pipeline uses the shared template. Pull requests always run a
read-only plan. A pull updates the private configuration repository and opens
a pull request. A push runs as a deployment to the selected environment.
Configure approvals on the production environment.

## Data boundaries

The repository stores ACS settings as JSON. It never stores HEC token values,
user records, or ACS tokens. Tokens come from environment variables at run
time.

## Wiki

- [Wiki home](wiki/Home.md)
- [Getting started](wiki/Getting-started.md)
- [File format](wiki/Reference/File-format.md)
- [Commands](wiki/Reference/Commands.md)
- [Object types](wiki/Reference/Object-types.md)
- [Copy between environments](wiki/Reference/Copy-between-environments.md)
- [Troubleshooting](wiki/Troubleshooting.md)
