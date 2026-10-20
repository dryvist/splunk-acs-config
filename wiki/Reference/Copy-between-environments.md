# Copy between environments

[Home](/Home) > [Reference](/Reference) > Copy between environments

[[_TOC_]]

Use `copy` to make one environment's overrides in the files match another
environment's overrides. The command changes files only. It does not call
ACS.

~~~text
python acs_config.py copy nonprod prod
python acs_config.py plan prod
~~~

For each selected object that the source environment includes:

- The target environment is added to the object's environments list, when the
  object has one.
- The target's overrides are replaced by the source's overrides. When the
  source has none, the target's override is removed.

Type defaults in _defaults.toml are handled the same way.

Use --types and --names to limit the objects. Use --dir when the config
directory is not the current directory.

## Steps

1. Run `copy` with the source and target environments.
2. Review the changed files in the diff.
3. Run `plan` for the target environment.
4. Merge the change to `main` through a pull request.
5. Run the pipeline with the `push` action for the target environment. Its
   deployment job waits for any approval on the environment.

## Verify

- Confirm the file diff contains the target environment values you expect.
- Confirm the plan reports only the intended differences.
- Confirm push ends with `NO DIFFERENCES after push`.

## Related

- [File format](/Reference/File-format)
- [Commands](/Reference/Commands)
- [Getting started](/Getting-started)

---

[< Previous: Object types](/Reference/Object-types) |
[Next: Push one object >](/Reference/Push-one-object)
