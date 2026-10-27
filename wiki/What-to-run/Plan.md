# Plan

A plan compares the repository files with the live stack, reports the differences, and changes nothing.

## Run the plan

1. Select **Pipelines**.
2. Open the config pipeline.
3. Select **Run pipeline**.
4. Set `action` to `plan`.
5. Set `environment` to `all`, `nonprod` or `prod`.
6. Set `types` to `all`, or to type names separated by `;`.
7. Set `names` to `all`, or to names separated by `;`.
8. Keep `check` as `false` to report differences only. Set it to `true` to fail the run when differences exist.
9. Select **Run**.
10. Wait for the run to finish.
11. Open the `Plan nonprod (repo vs live)` step.
12. Open the `Plan prod (repo vs live)` step.

## Verify the plan

1. Confirm both plan steps succeed.
2. Confirm each plan step prints `NO DIFFERENCES`.
3. Confirm the run has no push step.

A plan that prints `ONLY LIVE` needs a decision. See [Only live objects](/Troubleshooting/Only-live-objects).

## Nightly drift check

The nightly run is a plan with `check` on, for every environment, type and name. Its schedule is set up on
[Schedule the nightly plan](/Setup/Schedule).

When a nightly run fails with differences, open the failing plan step to read them, then choose one:

1. Read the live values into the repository with [Pull](/What-to-run/Pull), when the live values are correct.
2. Write the repository values to the stack with [Push](/What-to-run/Push), when the file values are correct.
