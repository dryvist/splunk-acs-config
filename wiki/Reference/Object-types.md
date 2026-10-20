# Object types

[Home](/Home) > [Reference](/Reference) > Object types

[[_TOC_]]

| Type | File | ACS resource | Pushed by default |
| --- | --- | --- | --- |
| indexes | `objects/indexes.toml` | /indexes | yes |
| hec-tokens | `objects/hec-tokens.toml` | /inputs/http-event-collectors | yes |
| ip-allowlists | `objects/ip-allowlists.toml` | `/access/<feature>/ipallowlists` | no |
| ip-allowlists-v6 | `objects/ip-allowlists-v6.toml` | `/access/<feature>/ipallowlists-v6` | no |
| outbound-ports | `objects/outbound-ports.toml` | /access/outbound-ports | no |
| outbound-ports-v6 | `objects/outbound-ports-v6.toml` | /access/outbound-ports-v6 | no |
| roles | `objects/roles.toml` | /roles | no |
| app-permissions | `objects/app-permissions.toml` | /permissions/apps | no |

A type marked no is pulled and documented. Plan and push skip it unless an
object or the `[default]` stanza sets `push = true`. See
[File format](/Reference/File-format).

## Stanza keys and stored data

- indexes uses the index name as the stanza name and stores writable index fields.
- hec-tokens uses the token name. Token values are never read, written, or printed.
- Both ip-allowlist types use the feature name and store a subnet list.
- Both outbound-ports types use the port number and store subnets. A configured
  reason is sent when creating a port; plans compare subnets.
- roles uses the role name and stores editable role fields.
- app-permissions uses the app name and stores read and write permissions.

## Data not stored

- User records and ACS credentials are not object data.
- App permissions do not create or delete apps.
- Built-in roles cannot be edited. The tool skips admin, can_delete, power,
  sc_admin, splunk-system-role, and user.

## Related

- [Commands](/Reference/Commands)
- [File format](/Reference/File-format)

---

[< Previous: Commands](/Reference/Commands) |
[Next: Copy between environments >](/Reference/Copy-between-environments)
