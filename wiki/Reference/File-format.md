# File format

[Home](/Home) > [Reference](/Reference) > File format

[[_TOC_]]

This page defines the TOML syntax and how configuration layers resolve.

## Files

`environments.toml` names environments and can limit the types used in an
environment. See [Object types](/Reference/Object-types) for type file names.

~~~toml
[nonprod]

[prod]
types = ["indexes", "app-permissions"]
~~~

Object values live under `[default]` and in named stanzas in
`objects/<type>.toml`. The stanza name is the object key and is not repeated as
a field. Quote names that contain punctuation.

~~~toml
[default]
maxDataSizeMB = 0
nonprod.searchableDays = 30

["my.index"]
searchableDays = 180
prod.unset = ["maxDataSizeMB"]
environments = ["nonprod", "prod"]
~~~

Lines beginning with `#` are comments. A pull rewrites type files, so comments
in those files are lost when the file changes.

## Layering

For an environment, each layer replaces fields set by earlier layers:

1. Built-in defaults and the type's default `push` value.
2. `[default]`.
3. `[default.<env>]`.
4. The object stanza.
5. `[<object>.<env>]`.

The `unset` list removes the named fields at its layer. An object with
`environments` applies only to the listed environments. An environment's
`types` list controls which types apply there. The merged result is the value
used by plan, push, and the generated inventory.

## App permission defaults

The app permission fields use the same layers:

~~~toml
[default]
read = ["*"]
write = ["sc_admin"]

[my_app]
write = ["team_role"]
~~~

Here `my_app` inherits `read` and replaces `write`.

## Pull behavior

A pull keeps explicit defaults and stores only values that differ from the
resolved layers above an object. When live data lacks an inherited field, the
pull records it in `unset`. A full pull may infer a shared default from the
live objects.

## Push scope

Push defaults are listed in [Object types](/Reference/Object-types). Set
`push` in a default or object layer to override the type default; the last
layer wins.

~~~toml
[my_app]
push = true
~~~

## Reserved names

`[default]` is reserved for type defaults. An object named `default` is an
error. Environment override names must exist in `environments.toml`; the tool
reports unknown tables with the file path. A separate `[my_app.prod]` table is
also accepted for older files.

---

[< Previous: Check plan](/Getting-started/Check-plan) |
[Next: Commands >](/Reference/Commands)
