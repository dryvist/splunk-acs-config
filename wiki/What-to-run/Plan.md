# Plan

A plan compares the repository files with the live stack, reports the differences, and changes nothing.

## Run the plan

1. Follow [Start a run](/What-to-run#start-a-run) with `write` cleared.
2. Wait for the run to finish.
3. Open the `Plan nonprod (repo vs live)` step.
4. Open the `Plan prod (repo vs live)` step.

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
