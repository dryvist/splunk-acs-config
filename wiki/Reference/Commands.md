# Commands

This page lists the command syntax, options and environment variables. The pipeline parameters are on
[What to run](/What-to-run#start-a-run).

## Syntax

Run the tool with Python 3.11 or later. Install the one dependency first: `python -m pip install tomlkit==0.15.2`.
Commands use the current directory unless you provide `--dir`.

~~~text
python acs_config.py pull <env|all> [--dir D] [--types "t1;t2"] [--names "n1;n2"] [--live-dir D]
python acs_config.py fetch <env> --out FILE [--dir D] [--types ...] [--names ...]
python acs_config.py plan <env> [--check] [--dir D] [--types ...] [--names ...]
python acs_config.py push <env> [--dir D] [--types ...] [--names ...] [--delete]
python acs_config.py doc [--dir D]
~~~

## Options

- `--dir D` sets the config directory.
- `--types` takes type names separated by `;`. `all` or an empty value selects every type.
- `--names` takes stanza names separated by `;`. `all` or an empty value selects every name.
- `--check` fails a plan when differences exist.
- `--delete` lets a push delete objects that exist only in the stack.
- `fetch` writes the live objects to `--out` as JSON and changes no files in the config directory.
- `pull all` pulls every environment. `--live-dir D` reads `D/live-<env>/<env>.json` from `fetch` instead of calling
  ACS.

## Environment variables

- The tool reads the token from `STACK_TOKEN`. The pipeline sets `STACK_TOKEN` from the `ACS_TOKEN` variable.
- `SPLUNK_STACK` names the stack.
- `SPLUNK_SEARCH_HEAD` is optional and is ignored when empty or unresolved.
- `SPLUNK_USERNAME` and `SPLUNK_PASSWORD` are used only when a Splunkbase app change is pushed.
  `SPLUNKBASE_USERNAME` and `SPLUNKBASE_PASSWORD` replace them when set.

The authorization token is sent in the ACS Bearer header. The variables are set in the variable groups described on
[Access and tokens](/Setup/Access-and-tokens).
