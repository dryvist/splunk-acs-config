# Copy nonprod to prod

Copy makes the prod overrides in the files match the nonprod overrides, without calling ACS.

## What copy changes

For each selected object that the source environment includes:

- The target environment is added to the object's `environments` list, when the object has one.
- The target's overrides are replaced by the source's overrides. When the source has none, the target's override is removed.

The `[default]` stanza and its `[default.<env>]` tables are handled the same way. Each type is one file, so a copy writes
one file per type it changes. For the file layers, see [File format](/Reference/File-format). For the options, see
[Commands](/Reference/Commands).

## Steps

1. Open a terminal in a local clone of the config repo.
2. Run `python acs_config.py copy nonprod prod`.
3. Review the changed files in the diff.
4. Run `python acs_config.py plan prod`.
5. Merge the change to `main` through a pull request. Follow the merge steps on [Pull](/What-to-run/Pull).
6. Push to `prod` as described on [Push](/What-to-run/Push).

## Verify

1. Confirm the file diff contains the target environment values you expect.
2. Confirm the plan reports only the intended differences.
