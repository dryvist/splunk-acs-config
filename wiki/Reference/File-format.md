# File format

This page defines the TOML syntax and how configuration layers resolve.

## Files

`environments.toml` names environments and can limit the types used in an environment. See
[Object types](/Reference/Object-types) for type file names. Set `archival = false` for a stack without Splunk Data
Archival. Plan and push then skip `splunkArchivalRetentionDays` in that environment.

~~~toml
[nonprod]
archival = false

[prod]
types = ["indexes", "app-permissions"]
~~~

Object values live under `[default]` and in named stanzas in `objects/<type>.toml`. The stanza name is the object key
and is not repeated as a field. Quote names that contain punctuation.

~~~toml
[default]
maxDataSizeMB = 0

[default.nonprod]
searchableDays = 30

["my.index"]
environments = ["nonprod", "prod"]
searchableDays = 180

["my.index".prod]
unset = ["maxDataSizeMB"]
~~~

You can also write `nonprod.searchableDays = 30` inside a stanza; both forms load the same, and a pull writes tables.
A pull writes a list of one or two items on one line, and a longer list with one item per line.

Lines beginning with `#` are comments. A pull rewrites type files, so comments in those files are lost when the file
changes.

## Layering

For an environment, each layer replaces fields set by earlier layers:

1. Built-in defaults and the type's default `push` value.
2. `[default]`.
3. `[default.<env>]`.
4. The object stanza.
5. `[<object>.<env>]`.

The `unset` list removes the named fields at its layer. An object with `environments` applies only to the listed
environments. An environment's `types` list controls which types apply there. The merged result is the value used by
plan, push, and the generated inventory.

## Pull behavior

Pull never writes or changes `[default]`; a person adds defaults there by hand. For each object field, pull compares
what each environment wants with what it inherits. If every environment wants the same value and at least one differs
from what it inherits, pull writes one object base line; if that value is missing, it writes one base `unset`. If
environments want different values, pull writes an override for each environment whose value differs from what it
inherits; a missing value is an environment `unset`. If no environment differs from what it inherits, pull writes no
line. A blank value counts as missing. On the next pull, object lines that a new `[default]` makes the same are removed.

## Push scope

Push defaults are listed in [Object types](/Reference/Object-types). Set `push = true` or `push = false` in a default
or object layer to override the type default; the last layer wins.

## Reserved names

`[default]` is reserved for type defaults. An object named `default` is an error. Environment override names must exist
in `environments.toml`; the tool reports unknown tables with the file path.
