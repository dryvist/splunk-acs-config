# Push

A push writes the repository settings to the stack, for one object, for one type, or for several types.

Each run on `main` has these stages:

1. **Plan (read-only):** plans each environment. It never writes.
2. **Push `<env>` (optional, run by hand):** one stage for each environment. It runs only when someone selects
   **Run stage**. It plans again, then writes the creates and updates. It never deletes. Any approval on the
   `splunk-<env>` environment also gates this stage.
3. **Delete `<env>` live-only objects (optional, run by hand):** only when `delete` is `true`. It runs only when
   someone selects **Run stage**.

A merge to `main` starts this run for every object. A pull request runs only the Plan stage.

## Push after a merge

1. Merge the file change to `main` through a pull request. Follow the merge steps on [Pull](/What-to-run/Pull).
2. Select **Pipelines**.
3. Open the config pipeline run for the merge.
4. Wait for the **Plan (read-only)** stage to finish.
5. Open **Plan nonprod** and confirm it lists only the objects you expect.
6. Select **Push nonprod (optional, run by hand)**.
7. Select **Run stage**.
8. Wait for the stage to finish.
9. Open the push step and confirm it ends with `NO DIFFERENCES after push`.
10. Repeat steps 5 to 9 for `prod`. Also approve the `splunk-prod` check when Azure DevOps asks.

## Push one object or type

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

1. Select **Pipelines**.
2. Open the config pipeline.
3. Select **Run pipeline**.
4. Set `action` to `push`, clear `readOnly`, and keep `delete` as `false`.
5. Set `types` and `names` from the table.
6. Select **Run**.
7. Follow steps 4 to 10 of [Push after a merge](#push-after-a-merge).
