# Commands

This page lists the command syntax, options, pipeline parameters and environment variables.

## Syntax

Run the tool with Python 3.11 or later. Commands use the current directory unless you provide `--dir`.

~~~text
python acs_config.py pull <env> [--dir D] [--types "t1;t2"] [--names "n1;n2"]
python acs_config.py plan <env> [--check] [--dir D] [--types ...] [--names ...]
python acs_config.py push <env> [--dir D] [--types ...] [--names ...] [--delete]
python acs_config.py copy <from-env> <to-env> [--dir D] [--types ...] [--names ...]
python acs_config.py doc [--dir D]
~~~

## Options

- `--dir D` sets the config directory.
- `--types` takes type names separated by `;`. `all` or an empty value selects every type.
- `--names` takes stanza names separated by `;`. `all` or an empty value selects every name.
- `--check` fails a plan when differences exist.
- `--delete` lets a push delete objects that exist only in the stack.

## Pipeline parameters

- `environment`: `all`, or one name from `environments.toml`.
- `action`: `plan`, `pull` or `push`.
- `types`: `all`, or type names separated by `;`. See [Object types](/Reference/Object-types).
- `names`: `all`, or stanza names separated by `;`.
- `check`: fails the plan when differences exist.
- `delete`: removes objects that exist only in the stack. Push only. See
  [Delete live-only objects](/What-to-run/Delete-live-only-objects).

## Environment variables

- `STACK_TOKEN` is used when set. Otherwise the tool uses `ACS_TOKEN`. The pipeline sets `STACK_TOKEN` from the
  `ACS_TOKEN` variable.
- `SPLUNK_STACK` names the stack.
- `SPLUNK_SEARCH_HEAD` is optional and is ignored when empty or unresolved.
- `SPLUNKBASE_USERNAME` and `SPLUNKBASE_PASSWORD` are used only when a Splunkbase app change is pushed.

The authorization token is sent in the ACS Bearer header. The variables are set in the variable groups described on
[Access and tokens](/Setup/Access-and-tokens).
