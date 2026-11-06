# Delete live-only objects

A delete removes objects that exist in the stack but not in the repository files.

Deleting an index deletes its data. Some types have no delete operation. See [Object types](/Reference/Object-types).

## Steps

1. Follow [Start a run](/What-to-run#start-a-run) with `action` set to `push`, and `delete` set to
   `true`. Set `environment`, `types` and `names` to the objects to check.
2. Wait for the **Plan (read-only)** stage to finish.
3. Read each `ONLY LIVE` and `REMOVE SUBNETS` line in the plan output.
4. If any object should stay, do not run any stage. Follow [Pull](/What-to-run/Pull) with the same `types` and
   `names`, then start again from step 1.
5. If every line should be removed, select **Delete `<env>` live-only objects (optional, run by hand)**.
6. Select **Run stage**.
7. Wait for the stage to finish.
8. Open the delete step and confirm it ends with `NO DIFFERENCES after push`.

## Verify

1. Run [Plan](/What-to-run/Plan) with the same `types` and `names`.
2. Confirm each `ONLY LIVE` line was pulled or removed as intended.
