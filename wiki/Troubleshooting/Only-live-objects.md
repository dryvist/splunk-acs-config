# ONLY LIVE objects

This page handles objects that exist in ACS but not in the files.

## Symptom

A plan reports ONLY LIVE for an object that is present in ACS but absent from the repository. An index whose values
are all Splunk defaults never shows as ONLY LIVE.

## Action

Review the object, then choose one:

1. Pull it into the repository to keep it managed. See [Pull](/What-to-run/Pull).
2. Remove it from ACS. See [Delete live-only objects](/What-to-run/Delete-live-only-objects).

A push without `delete` does not remove the object. The push then fails with `N differences remain after push`.

## Verify

Run [Plan](/What-to-run/Plan) again and confirm each ONLY LIVE line was pulled or removed as intended.
