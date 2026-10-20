# Object types

[Home](/Home) > [Reference](/Reference) > Object types

[[_TOC_]]

| Type | ACS resource |
| --- | --- |
| indexes | /indexes |
| hec-tokens | /inputs/http-event-collectors |
| ip-allowlists | `/access/<feature>/ipallowlists` |
| ip-allowlists-v6 | `/access/<feature>/ipallowlists-v6` |
| outbound-ports | /access/outbound-ports |
| outbound-ports-v6 | /access/outbound-ports-v6 |
| roles | /roles |
| app-permissions | /permissions/apps |

## File keys and stored data

- indexes uses name and stores writable index fields.
- hec-tokens uses spec.name. Token values are never read, written, or printed.
- Both ip-allowlist types use feature and store a subnet list.
- Both outbound-ports types use port and store subnets and a reason.
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
