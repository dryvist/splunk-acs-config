# Splunk Cloud ACS configuration

Each file in `objects/` holds one object type. `[default]` holds shared values; each stanza holds only what differs.

| Type | File | Pushed by default | nonprod | prod |
| --- | --- | --- | --- | --- |
| indexes | `objects/indexes.toml` | yes | 5 | 6 |
| hec-tokens | `objects/hec-tokens.toml` | yes | 2 | 2 |
| ip-allowlists | `objects/ip-allowlists.toml` | no | 2 | 2 |
| ip-allowlists-v6 | `objects/ip-allowlists-v6.toml` | no | 0 | 0 |
| outbound-ports | `objects/outbound-ports.toml` | no | 1 | 1 |
| outbound-ports-v6 | `objects/outbound-ports-v6.toml` | no | 0 | 0 |
| roles | `objects/roles.toml` | no | 1 | 1 |
| limits | `objects/limits.toml` | no | 0 | 0 |
| app-permissions | `objects/app-permissions.toml` | yes | 1 | 1 |

## indexes

- datatype: event (Splunk default)
- maxDataSizeMB: 0 (Splunk default)
- searchableDays: 90 (Splunk default)
- searchableDays: 30 (nonprod, [default])

## hec-tokens

- disabled: false (Splunk default)
- useAck: false (Splunk default)

## ip-allowlists

- none

## ip-allowlists-v6

- none

## outbound-ports

- none

## outbound-ports-v6

- none

## roles

- srchDiskQuota: 100 (Splunk default)
- srchJobsQuota: 3 (Splunk default)
- rtSrchJobsQuota: 6 (Splunk default)

## limits

- none

## app-permissions

- none
