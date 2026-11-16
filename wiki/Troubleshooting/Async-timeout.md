# ACS async timeout

This page fixes changes that stay pending after ACS accepts a write.

## Symptom

Push reports `timed out waiting for <type>/<key> to match the files`. ACS returned HTTP 202 for the change, or did
not answer the write in 60 seconds, and the object still differs from the files after 15 minutes of checks. The wait
between checks doubles from 10 seconds up to 60 seconds.

Push prints one error for each change that fails, goes on to the next change, and fails at the end.

## Action

1. Run [Plan](/What-to-run/Plan) with the same `types` and `names` to check the current live state.
2. If the change is still pending, wait and run the plan again.
3. Run the push again only when the plan still shows the change and the earlier operation has finished.

## Verify

1. The object's live state is visible in a new plan.
2. The plan prints `NO DIFFERENCES` for the object.
3. The push is not sent again while the first operation is pending.
