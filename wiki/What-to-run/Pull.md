# Pull

A pull reads the live stack into the repository files and opens one pull request with the changes.

## Run the pull

1. Follow [Start a run](/What-to-run#start-a-run) with `action` set to `pull` and `write` selected.
2. Wait for the run to finish.

## What a pull writes

- One `Read <env> live` job per environment reads ACS. The read jobs run in parallel.
- One `Pull <environment> into one pull request` job writes the reads to one branch, `acs-pull/<build id>`, and opens
  one pull request.
- See [File format](/Reference/File-format) for what a pull writes to type files.

## Verify the run

1. Confirm the `Read <env> live` jobs run at the same time, and the pull job starts after all of them finish.
2. Confirm the `Publish <environment> settings as a pull request` step prints a pull request link, or
   `Pull request for acs-pull/<build id> is already open`.
3. Confirm a run with no changes prints `NO DIFFERENCES` and opens no pull request.
4. Confirm no step in the run is a push step.

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
