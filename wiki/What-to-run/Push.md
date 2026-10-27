# Push

A push writes the repository settings to the stack, for one object, for one type, or for several types.

Push runs only when you start the pipeline with `action` set to `push`. Commits and pull requests never push. Each
environment runs one deployment job, on the environment `splunk-<env>`. An approval on that environment gates the job.

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
6. Set `action` to `plan`.
7. Set `types` and `names` from the table.
8. Select **Run**.
9. Wait for the run to finish.
10. Open the plan step and confirm it lists only the objects you expect.
11. Select **Run pipeline**.
12. Keep `environment`, `types` and `names`. Set `action` to `push`, and keep `delete` as `false`.
13. Select **Run**.
14. Wait for the run to finish.
15. Open the push step and confirm it ends with `NO DIFFERENCES after push`.
16. Repeat steps 2 to 15 with `environment` set to `prod`. The prod push waits for approval. Approve the `splunk-prod`
    check when Azure DevOps asks.

## Verify

1. Confirm the prod push waited for the approval before it ran.
2. Confirm the prod push ends with `NO DIFFERENCES after push`.
