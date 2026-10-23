# File format

[Home](/Home) > [Reference](/Reference) > File format

[[_TOC_]]

## Layout

~~~text
environments.toml
objects/<type>.toml
README.md
~~~

Each object type is one file, for example `objects/indexes.toml`. The file reads
like a Splunk `.conf` file. A `[default]` stanza comes first, then one stanza
per object. Each stanza holds only the fields that differ from the layers above
it. A line that starts with an environment name, such as
`nonprod.searchableDays`, applies to that environment only.

~~~toml
[default]
nonprod.searchableDays = 30     # every index in nonprod

[aws]                           # empty stanza: uses every default

[network]
environments = ["prod"]         # absent = every environment

[wineventlog]
searchableDays = 180            # every environment
nonprod.searchableDays = 60     # this object, nonprod only
nonprod.unset = ["selfStorageBucketPath"]
~~~

A pull writes the fewest lines that give each environment its live values. A
value shared by every environment of an object is written once, without an
environment name. A field that most objects do not have never becomes a
default.

The stanza name is the object key: the index name, HEC token name, allowlist
feature, outbound port, role name, limits stanza, or app name. TOML quotes a
name when it needs to, for example `["my.index"]`. The key is not repeated
inside the stanza. The tool adds it when it reads the file, and it stores a
port as a number.

Comments starting with `#` are allowed. A pull rewrites the type files, so a
comment is lost on the next pull.

Each environment is a top-level table. An environment can limit its types:

~~~toml
[nonprod]

[prod]

[limited]
types = ["roles", "app-permissions"]
~~~

## Reserved names

- `[default]` is reserved. An object named `default` is an error.
- A line such as `nonprod.searchableDays` under `[default]` or under an object
  is an environment override. Its environment must be listed in
  `environments.toml`. Any other name is an error that names the file and the
  table, for example `pan.staging`. The older form, a separate
  `[pan.nonprod]` table, still reads the same way.
- A file whose `default` value is not a table is an error.

## Built-in Splunk defaults

The tool knows these defaults. They are the lowest layer, so a file shows only
deviations from stock Splunk.

| Type | Field | Value | Source |
| --- | --- | --- | --- |
| indexes | datatype | `"event"` | ACS OpenAPI `IndexInfo` |
| indexes | maxDataSizeMB | `0` | ACS OpenAPI `IndexInfo` |
| indexes | searchableDays | `90` | ACS OpenAPI `IndexInfo` |
| hec-tokens | disabled | `false` | `inputs.conf.spec` `[http://<name>]`, Splunk 10.6 |
| hec-tokens | useAck | `false` | `inputs.conf.spec` `useACK`, Splunk 10.6 |
| roles | srchDiskQuota | `100` | `authorize.conf` `[default]`, Splunk 10.6 |
| roles | srchJobsQuota | `3` | `authorize.conf` `[default]`, Splunk 10.6 |
| roles | rtSrchJobsQuota | `6` | `authorize.conf` `[default]`, Splunk 10.6 |

The cumulative role quotas are not in the ACS OpenAPI `RolesInfo` schema, so
they have no built-in default. The OpenAPI schema is the source where it
defines a default. Otherwise the source is the Splunk `.conf` specification
files at version 10.6.

## Layering

The effective fields for environment E are combined in this order. Each layer
replaces the fields it sets from the layers before it:

1. The built-in Splunk defaults, and the type's push default.
2. `[default]`.
3. `[default.<E>]`.
4. The object's stanza.
5. `[<object>.<E>]`.

Each layer replaces a whole field value. An `unset = ["field"]` list in a layer
removes that field for the environment. A pull writes it when a field is set in
the base but missing live. The object exists only in the environments named by
its `environments` field. The environment's `types` list limits which object
types are included.

## Defaults written by a pull

A pull writes defaults only where none exist. It never changes a default that is
already set, so hand-set defaults stay as written.

- When `[default]` has no fields, each field is set to the most common live value
  in that environment, where that value differs from the built-in Splunk default.
  A tie goes to the value whose JSON text sorts first.
- When `[default.<E>]` does not exist, it is added with each field whose most
  common live value in E differs from the layers above it. Nothing is written when
  no field differs.
- A pull that selects objects with **Object names** writes no defaults.
- The ip-allowlists and outbound-ports types never get inferred defaults.

After the defaults, a pull writes each object's stanza with only the fields that
differ from the layers above it. An object that exists in every environment has
no `environments` line.

## Push scope

Pull and doc read every type. Plan and push compare and write only objects
whose `push` flag is true. indexes, hec-tokens, and app-permissions default to
`push = true`; every other type defaults to `push = false`, so the remaining
types are documented but not written by default.

Set `push` in `[default]` to change a whole type, or in one stanza to change
that object. Set it in `[default.<E>]` or `[<object>.<E>]` to change one
environment. The last layer wins.

~~~toml
[pan_analyst]
push = true
~~~

## App permission inheritance

~~~toml
[default]
read = ["*"]
write = ["admin", "sc_admin"]

[search]

[my_app]
write = ["sc_admin", "my_role"]
~~~

The `search` app inherits both `read` and `write` from `[default]`.

## Splunkbase app versions

~~~toml
[my_app]
id = "12345"
version = "1.0.0"
license = "<license URL>"

[my_app.prod]
version = "1.1.0"
~~~

## Worked example

With the example above, the effective searchableDays values are:

- aws in nonprod: 30, from `nonprod.searchableDays` in `[default]`.
- aws in prod: 90, from the built-in Splunk default.
- wineventlog in prod: 180, from its stanza.
- wineventlog in nonprod: 60, from `nonprod.searchableDays` in `[wineventlog]`.
- network: set only in prod, because of its `environments` line.

## Related

- [Commands](/Reference/Commands)
- [Object types](/Reference/Object-types)

---

[< Previous: Check plan](/Getting-started/Check-plan) |
[Next: Commands >](/Reference/Commands)
