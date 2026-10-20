# ACS async timeout

[Home](/Home) > [Troubleshooting](/Troubleshooting) > Async timeout

[[_TOC_]]

## Symptom

ACS returns HTTP 202, but the operation does not finish before the client
timeout.

## Action

Run plan to check the current live state before retrying the operation. If the
operation is still pending, wait for it to finish and plan again.

## Verify

- The operation's final state is visible in a new plan.
- No duplicate change is sent while the first operation is pending.

## Related

- [Commands](/Reference/Commands)
- [Authentication](/Troubleshooting/Authentication)

---

[< Previous: ACS allowlist](/Troubleshooting/ACS-allowlist) |
[Next: Built-in roles >](/Troubleshooting/Built-in-roles)
