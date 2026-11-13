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
  - A pull skips a new index whose values are all Splunk defaults, such as system and app indexes. Plan and push
    ignore it. To manage one, add its stanza by hand.
  - `mdlIndex`, `selfStorageBucketPath`, and `splunkArchivalRetentionDays` are written only when set. They never go
    in `[default]` or `unset`.
- hec-tokens uses the token name.
  - When the files leave `defaultHost` unset, plan does not compare it, and each HEC create sends it blank.
  - An update sends it blank only when the live value is the stack default, `<stack>.splunkcloud.com` or
    `<host>.<stack>.splunkcloud.com`.
  - A pull does not store a `defaultHost` that is the stack default.
  - Token values are never written to files or sent to ACS. Push prints the token value of each HEC token it creates
    or updates.
- Both ip-allowlist types use the feature name and store a subnet list.
- Both outbound-ports types use the port number and store subnets. A configured reason is sent when creating a port;
  plans compare subnets.
- roles uses the role name and stores editable role fields.
- limits uses the stanza name and stores editable settings. ACS has no delete endpoint for limits.
- app-permissions uses the app name and stores read and write permissions plus the repository-only `owner` value.
- private-apps uses the app name and stores its installed version.
- splunkbase-apps uses the app name and stores its id, version, and license URL.

## Splunkbase apps

Pull records the app name, id, and version. Plans compare only version. ACS installs or updates a Splunkbase app only when the push
sends the app's license URL. Set `license` to that URL, or to `"splunkbase"` to send the license URL Splunkbase lists
for the app. `license = "splunkbase"` in `[default]` covers every app; it means you accept each app's license. This type has no delete operation.

Change `version` to upgrade or downgrade an app. Set `version = "latest"` to keep an app on its newest cloud-compatible
release: plan and push read Splunkbase's public release list and use that exact version, and a pull keeps `"latest"`.

## Search head targets

ACS app permissions apply to the targeted search head. Add one environment per search head for app permissions; each
environment's variable group can set its own `SPLUNK_SEARCH_HEAD`.

## Sharing

App sharing (private, app, global, and `export = system`) is not in ACS. Set it in each app's `metadata/default.meta` and
deploy it with the app.

## Data not stored

- User records and ACS credentials are not object data.
- App permissions do not create or delete apps.
- The tool skips the built-in roles admin, apps, can_delete, list_users_roles, power, sc_admin, splunk-system-role,
  tokens_auth and user, and every role that starts with ess_ (ES), is4s_ or itoa_ (ITSI). See
  [Built-in roles](/Troubleshooting/Built-in-roles).
