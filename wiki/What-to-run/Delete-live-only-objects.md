# Delete live-only objects

A delete removes objects that exist in the stack but not in the repository files.

Deleting an index deletes its data. Some types have no delete operation. See [Object types](/Reference/Object-types).

## Steps

1. Select **Pipelines**.
2. Open the config pipeline.
3. Select **Run pipeline**.
4. Set `action` to `plan`.
5. Set `environment`, `types` and `names` to the objects to check.
6. Select **Run**.
7. Wait for the run to finish.
8. Read each `ONLY LIVE` line in the plan output.
9. For each object to keep, follow [Pull](/What-to-run/Pull) with the same `types` and `names`.
10. For each object to remove, select **Run pipeline**.
11. Set `action` to `push`, and set `delete` to `true`.
12. Set `environment`, `types` and `names` to that object.
13. Select **Run**.
14. Wait for the run to finish.
15. Open the push step and confirm it ends with `NO DIFFERENCES after push`.

## Verify

1. Run [Plan](/What-to-run/Plan) with the same `types` and `names`.
2. Confirm each `ONLY LIVE` line was pulled or removed as intended.
