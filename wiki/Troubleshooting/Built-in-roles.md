# Built-in roles

[Home](/Home) > [Troubleshooting](/Troubleshooting) > Built-in roles

[[_TOC_]]

## Symptom

A plan does not show a change for a built-in role, or a built-in role
is not in objects/roles.

## Cause

ACS does not allow built-in roles to be edited. The tool skips admin,
can_delete, power, sc_admin, splunk-system-role, and user in plan output.
It reports no change and no ONLY LIVE line for them.

## Verify

Run plan and confirm the built-in roles do not appear in the output.

## Related

- [Object types](/Reference/Object-types)
- [Commands](/Reference/Commands)

---

[< Previous: Async timeout](/Troubleshooting/Async-timeout) |
[Next: Pull request permission >](/Troubleshooting/Pull-request-permission)
