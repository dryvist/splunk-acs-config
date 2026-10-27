# Object types

This page lists the managed object types, their files, and their ACS fields.

| Type | File | ACS resource | Pushed by default |
| --- | --- | --- | --- |
| indexes | `objects/indexes.toml` | /indexes | yes |
| hec-tokens | `objects/hec-tokens.toml` | /inputs/http-event-collectors | yes |
| ip-allowlists | `objects/ip-allowlists.toml` | `/access/<feature>/ipallowlists` | no |
| ip-allowlists-v6 | `objects/ip-allowlists-v6.toml` | `/access/<feature>/ipallowlists-v6` | no |
| outbound-ports | `objects/outbound-ports.toml` | /access/outbound-ports | no |
| outbound-ports-v6 | `objects/outbound-ports-v6.toml` | /access/outbound-ports-v6 | no |
| roles | `objects/roles.toml` | /roles | no |
| limits | `objects/limits.toml` | /limits | no |
| app-permissions | `objects/app-permissions.toml` | /permissions/apps | yes |
| private-apps | `objects/private-apps.toml` | /apps/victoria?splunkbase=false&count=0 | no |
| splunkbase-apps | `objects/splunkbase-apps.toml` | /apps/victoria?splunkbase=true&count=0 | yes |

A type marked no is not pushed by default. See [File format](/Reference/File-format) for `push` settings.

## Stanza keys and stored data

- indexes uses the index name as the stanza name and stores writable index fields.
- hec-tokens uses the token name. Token values are never read, written, or printed.
- Both ip-allowlist types use the feature name and store a subnet list.
- Both outbound-ports types use the port number and store subnets. A configured reason is sent when creating a port;
  plans compare subnets.
- roles uses the role name and stores editable role fields.
- limits uses the stanza name and stores editable settings. ACS has no delete endpoint for limits.
- app-permissions uses the app name and stores read and write permissions plus the repository-only `owner` value.
- private-apps uses the app name and stores its installed version.
- splunkbase-apps uses the app name and stores its id, version, and license URL.

## Splunkbase apps

Pull records the app name, id, and version. Plans compare only version. If ACS reports a missing license, copy the URL
from the error into `license`. This type has no delete operation.

## Search head targets

ACS app permissions apply to the targeted search head. Add one environment per search head for app permissions; each
environment's variable group can set its own `SPLUNK_SEARCH_HEAD`.

## Sharing

App sharing (private, app, global, and `export = system`) is not in ACS. Set it in each app's `metadata/default.meta` and
deploy it with the app.

## Data not stored

- User records and ACS credentials are not object data.
- App permissions do not create or delete apps.
- The tool skips the built-in roles admin, can_delete, power, sc_admin, splunk-system-role, and user. See
  [Built-in roles](/Troubleshooting/Built-in-roles).
