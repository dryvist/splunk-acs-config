# Object types

[Home](/Home) > [Reference](/Reference) > Object types

[[_TOC_]]

| Type | ACS resource | Pushed by default |
| --- | --- | --- |
| indexes | /indexes | yes |
| hec-tokens | /inputs/http-event-collectors | yes |
| ip-allowlists | `/access/<feature>/ipallowlists` | no |
| ip-allowlists-v6 | `/access/<feature>/ipallowlists-v6` | no |
| outbound-ports | /access/outbound-ports | no |
| outbound-ports-v6 | /access/outbound-ports-v6 | no |
| roles | /roles | no |
| app-permissions | /permissions/apps | no |

A type marked no is pulled and documented. Plan and push skip it unless an
object or `_defaults.toml` sets `push = true`. See
[File format](/Reference/File-format).

## File keys and stored data

- indexes uses name and stores writable index fields.
- hec-tokens uses name. Token values are never read, written, or printed.
- Both ip-allowlist types use feature and store a subnet list.
- Both outbound-ports types use port and store subnets. A configured reason is
  sent when creating a port; plans compare subnets.
- roles uses name and stores editable role fields.
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
