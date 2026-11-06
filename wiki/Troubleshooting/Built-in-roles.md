# Built-in roles

This page explains why built-in role changes do not appear in plans.

## Symptom

A plan does not show a change for a built-in role, or a built-in role is not in `objects/roles.toml`.

## Cause

The tool skips built-in roles and premium app roles, so they cannot be changed by mistake. It reports no change and no
ONLY LIVE line for them. A skipped role found in `objects/roles.toml` prints a `skipped` warning; delete that stanza.
The skipped names are listed on [Object types](/Reference/Object-types).

## Verify

Run [Plan](/What-to-run/Plan) and confirm the built-in roles do not appear in the output.
