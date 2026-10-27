# Pull

A pull reads the live stack into the repository files and opens one pull request with the changes.

## Run the pull

1. Select **Pipelines**.
2. Open the config pipeline.
3. Select **Run pipeline**.
4. Set `action` to `pull`.
5. Set `environment` to `all`, `nonprod` or `prod`.
6. Set `types` to `all`, or to type names separated by `;`.
7. Set `names` to `all`, or to names separated by `;`.
8. Leave `check` and `delete` as `false`. A pull ignores both.
9. Select **Run**.
10. Wait for the run to finish.

## What a pull writes

- With `environment` set to `all`, the environments run in reverse name order, so `prod` runs before `nonprod`.
- Every environment commits to one branch, `acs-pull/<build id>`, with one pull request.
- The first environment pulled sets the `[default]` stanza of each type, when it is empty, and each object's base values.
- Later environments add `[default.<env>]` and object overrides only where they differ.

For the file layers, see [File format](/Reference/File-format).

## Verify the run

1. Confirm the `Pull nonprod` job starts after the `Pull prod` job finishes.
2. Confirm the `Publish <env> settings as a pull request` step of a job with changes prints a pull request link, or
   `Pull request for acs-pull/<build id> is already open`.
3. Confirm a run with no changes prints `NO DIFFERENCES` and opens no pull request.
4. Expand the groups in the `Show <env> objects created, changed or deleted by this pull` step. Each group is one
   changed file, such as `objects/indexes.toml (3 objects)`, with one line per object, such as `changed [pan] 1 fields`.
5. Confirm no step in the run is a push step.

If the publish step gets HTTP 403, see [Pull request permission](/Troubleshooting/Pull-request-permission).

## Merge the pull request

1. Select **Repos**.
2. Select **Pull requests**.
3. Open the pull request whose source branch starts with `acs-pull/`.
4. Select **Files**.
5. Review the changed files.
6. Confirm no changed file contains a token value. See [Access and tokens](/Setup/Access-and-tokens).
7. Wait for the Build validation run on the pull request to succeed.
8. Select **Complete**.
9. Select **Complete merge**.

## Verify the merge

1. Confirm the pull request shows **Completed**.
2. Confirm `main` contains one file per object type under `objects/`, with each pulled environment's values in its
   stanzas. See [Object types](/Reference/Object-types).
