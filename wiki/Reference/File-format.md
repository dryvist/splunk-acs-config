# File format

[Home](/Home) > [Reference](/Reference) > File format

[[_TOC_]]

## Layout

~~~text
environments.toml
objects/<type>/_defaults.toml
objects/<type>/<key>.toml
README.md
~~~

Each object file is a TOML table. Its fields hold ACS writable values. The
optional environments list limits that object to the named environments.
Without the list, the object is included in every environment.

Each environment is a top-level table. An environment can limit its types:

~~~toml
[nonprod]

[prod]

[limited]
types = ["roles", "app-permissions"]
~~~

Comments starting with `#` are allowed. A pull rewrites object files, so a
comment inside an object file is lost on the next pull.

## Layering

The effective fields for environment E are combined in this order:

1. Type defaults from objects/`<type>`/_defaults.toml.
2. Default overrides for E.
3. The object's base fields.
4. The object's overrides for E.

Each layer replaces a whole field value. An `unset = ["field"]` list in an
override removes those fields for that environment; a pull writes it when a
field is set in the base but missing live. The object exists only in an
environment allowed by its environments field. The environment's types list
limits which object types are included.

## Push scope

Pull and doc read every type. Plan and push compare and write only objects
whose `push` flag is true. indexes and hec-tokens default to `push = true`; every
other type defaults to `push = false`, so settings that Splunk apps manage are
documented but never written.

Set `push` in `_defaults.toml` to change a whole type, or in one object file
to change that object. Put the line above any `[overrides...]` table, or set
it inside `[overrides.<env>]` for one environment. The last layer wins.

~~~toml
name = "pan_analyst"
push = true
~~~

## Worked example

The shipped example sets an indexes default of 90 searchable days, with 30 in
nonprod.

~~~toml
datatype = "event"
maxDataSizeMB = 0
searchableDays = 90

[overrides.nonprod]
searchableDays = 30
~~~

The pan object sets no fields of its own, so it inherits the default.

~~~toml
name = "pan"
~~~

The wineventlog object replaces the default in both environments.

~~~toml
name = "wineventlog"
searchableDays = 180
~~~

The effective searchableDays values are:

- pan in nonprod: 30, from the default override.
- pan in prod: 90, from the default.
- wineventlog in both environments: 180, from the object.

## File names

The file name is the object's ACS key. A slash or colon in a key is replaced
by an underscore in the file name. The key remains in TOML as name,
feature, or port.

## Related

- [Commands](/Reference/Commands)
- [Object types](/Reference/Object-types)

---

[< Previous: Check plan](/Getting-started/Check-plan) |
[Next: Commands >](/Reference/Commands)
