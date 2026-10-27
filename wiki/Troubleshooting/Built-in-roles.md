# Built-in roles

[Home](/Home) > [Troubleshooting](/Troubleshooting) > Built-in roles

[[_TOC_]]

This page explains why built-in role changes do not appear in plans.

## Symptom

A plan does not show a change for a built-in role, or a built-in role
is not in objects/roles.toml.

## Cause

ACS does not allow built-in roles to be edited, so the tool skips them. It
reports no change and no ONLY LIVE line for them. The skipped names are listed
on [Object types](/Reference/Object-types).

## Verify

Run plan and confirm the built-in roles do not appear in the output.

## Related

- [Object types](/Reference/Object-types)
- [Commands](/Reference/Commands)

---

[< Previous: Async timeout](/Troubleshooting/Async-timeout) |
[Next: Pull request permission >](/Troubleshooting/Pull-request-permission)
