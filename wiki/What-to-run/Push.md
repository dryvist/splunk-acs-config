# Push

A push writes the repository settings to the stack, for one object, for one type, or for several types.

Push runs only when you start the pipeline with `action` set to `push`. Commits and pull requests never push.

A push run has these stages:

1. **Plan (read-only):** plans each environment. It never writes.
2. **Push `<env>`:** one stage for each environment, after the Plan stage. Its jobs run in this order:
   1. **Approve push to `<env>`** waits until someone selects **Resume** or **Reject**.
   2. **Push `<env>` creates and updates** writes the plan's creates and updates. It never deletes. Any approval
      on the `splunk-<env>` environment also gates this stage.
   3. When `delete` is `true`, **Approve delete in `<env>`** waits for a second approval. Then **Delete `<env>`
      live-only objects** deletes them.

## Choose the values

| Goal | `types` | `names` |
| --- | --- | --- |
| Index `pan` | `indexes` | `pan` |
| HEC token `aws_firehose` | `hec-tokens` | `aws_firehose` |
| IPv4 allowlist for HEC | `ip-allowlists` | `hec` |
| Outbound port 8089 | `outbound-ports` | `8089` |
| Role `pan_analyst` | `roles` | `pan_analyst` |
| App permissions | `app-permissions` | The app folder name |
| Push a type | One type name, or several separated by `;` | `all` |

Each name is a stanza name in the type's file. Separate several names with `;`. The type names are on
[Object types](/Reference/Object-types).

## Steps

1. Merge the file change to `main` through a pull request. Follow the merge steps on [Pull](/What-to-run/Pull).
2. Select **Pipelines**.
3. Open the config pipeline.
4. Select **Run pipeline**.
5. Set `environment` to `nonprod`.
6. Set `action` to `push`, and keep `delete` as `false`.
7. Set `types` and `names` from the table.
8. Select **Run**.
9. Wait for the **Plan (read-only)** stage to finish.
10. Open **Plan nonprod** and confirm it lists only the objects you expect.
11. Open the **Approve push to nonprod** job.
12. Select **Resume** if the plan is right. Select **Reject** if it is not.
13. Wait for the run to finish.
14. Open the push step and confirm it ends with `NO DIFFERENCES after push`.
15. Repeat steps 2 to 14 with `environment` set to `prod`. Also approve the `splunk-prod` check when Azure DevOps
    asks.

## Verify

1. Confirm the prod push waited for both approvals before it ran.
2. Confirm the prod push ends with `NO DIFFERENCES after push`.
