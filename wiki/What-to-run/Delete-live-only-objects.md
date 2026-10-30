# Delete live-only objects

A delete removes objects that exist in the stack but not in the repository files.

Deleting an index deletes its data. Some types have no delete operation. See [Object types](/Reference/Object-types).

## Steps

1. Select **Pipelines**.
2. Open the config pipeline.
3. Select **Run pipeline**.
4. Set `action` to `push`, and set `delete` to `true`.
5. Set `environment`, `types` and `names` to the objects to check.
6. Select **Run**.
7. Wait for the **Plan (read-only)** stage to finish.
8. Read each `ONLY LIVE` and `REMOVE SUBNETS` line in the plan output.
9. If any object should stay, select **Reject** in **Approve push to `<env>`**. Follow [Pull](/What-to-run/Pull)
   with the same `types` and `names`, then start again from step 1.
10. If every line should be removed, select **Resume** in **Approve push to `<env>`**.
11. Wait for the push job to finish.
12. Select **Resume** in **Approve delete in `<env>`**.
13. Wait for the run to finish.
14. Open the delete step and confirm it ends with `NO DIFFERENCES after push`.

## Verify

1. Run [Plan](/What-to-run/Plan) with the same `types` and `names`.
2. Confirm each `ONLY LIVE` line was pulled or removed as intended.
