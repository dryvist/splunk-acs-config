# Commands

[Home](/Home) > [Reference](/Reference) > Commands

[[_TOC_]]

Run the tool with Python 3.11 or later. Commands use the current directory
unless you provide --dir.

~~~text
python acs_config.py pull <env> [--dir D] [--types "t1 t2"] [--names "n1 n2"]
python acs_config.py plan <env> [--dir D] [--types ...] [--names ...]
python acs_config.py push <env> [--dir D] [--types ...] [--names ...] [--delete]
python acs_config.py copy <from-env> <to-env> [--dir D] [--types ...] [--names ...]
python acs_config.py doc [--dir D]
~~~

An empty filter or all selects every type or name. The push --delete option
allows live-only objects to be deleted. Review the plan before enabling it.

## Environment variables

- STACK_TOKEN is used when set; otherwise the tool uses ACS_TOKEN.
- SPLUNK_STACK names the stack.
- SPLUNK_SEARCH_HEAD is optional and is ignored when empty or unresolved.

The authorization token is sent in the ACS Bearer header. It belongs in a
secret variable group or the local environment, not in a TOML file.

## Pipeline actions

- plan compares repository settings with live settings.
- pull updates the files for an environment. The pipeline opens a pull request
  when files change.
- push applies repository settings through a deployment job on environment
  `splunk-<env>`. Any approval configured on that environment gates the job.
  The example pipeline does not push on a commit or pull request.
- copy sets the target environment overrides in the files to match the source,
  without calling ACS.
- doc renders the configuration documentation.

## Related

- [File format](/Reference/File-format)
- [Copy between environments](/Reference/Copy-between-environments)
- [Troubleshooting](/Troubleshooting)

---

[< Previous: File format](/Reference/File-format) |
[Next: Object types >](/Reference/Object-types)
