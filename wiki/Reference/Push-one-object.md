# Push one object

[Home](/Home) > [Reference](/Reference) > Push one object

[[_TOC_]]

A push changes only the objects that match **Object types** and **Object
names**. Use them to apply one index, one HEC token, one allowlist feature,
one outbound port, one role, or one app's permissions.

| Object | Object types | Object names |
| --- | --- | --- |
| Index `pan` | `indexes` | `pan` |
| HEC token `aws_firehose` | `hec-tokens` | `aws_firehose` |
| IPv4 allowlist for HEC | `ip-allowlists` | `hec` |
| Outbound port 8089 | `outbound-ports` | `8089` |
| Role `pan_analyst` | `roles` | `pan_analyst` |
| App permissions | `app-permissions` | the app folder name |

Separate several names with spaces, for example `pan wineventlog`.

## Steps

1. Merge the file change to `main` through a pull request.
2. Open the config pipeline.
3. Select **Run pipeline**.
4. Type `nonprod` as **Environment**.
5. Select `plan` as **Action**.
6. Type the type as **Object types**, for example `indexes`.
7. Type the name as **Object names**, for example `pan`.
8. Select **Run**.
9. Confirm the plan lists only the object you expect.
10. Repeat steps 3 to 8 with `push` as **Action**.
11. Confirm the push ends with `NO DIFFERENCES after push`.
12. Repeat steps 3 to 11 with `prod` as **Environment**.
13. Approve the `splunk-prod` environment check when Azure DevOps asks.

**Verify:**

1. Confirm the prod push waited for the approval before it ran.
2. Confirm the prod push ends with `NO DIFFERENCES after push`.

Leave **Delete live-only objects** unchecked unless the object should be
removed. Deleting an index deletes its data.

## Related

- [Commands](/Reference/Commands)
- [Copy between environments](/Reference/Copy-between-environments)

---

[< Previous: Copy between environments](/Reference/Copy-between-environments) |
[Next: Troubleshooting >](/Troubleshooting)
