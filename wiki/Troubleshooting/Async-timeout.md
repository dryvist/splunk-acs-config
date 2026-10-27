# ACS async timeout

[Home](/Home) > [Troubleshooting](/Troubleshooting) > Async timeout

[[_TOC_]]

This page checks changes that remain pending after ACS accepts a write.

## Symptom

Push reports `timed out waiting for <type>/<key> to match the files`. ACS
returned HTTP 202 for the change, and the object still differs from the files
after 15 minutes of polling.

## Action

Run plan with the same types and names to check the current live state. If the
change is still pending, wait and plan again. Run push again only when plan
still shows the change and the earlier operation has finished.

## Verify

- The object's live state is visible in a new plan.
- Plan prints NO DIFFERENCES for the object.
- Push is not sent again while the first operation is pending.

## Related

- [Commands](/Reference/Commands)
- [Authentication](/Troubleshooting/Authentication)

---

[< Previous: ACS allowlist](/Troubleshooting/ACS-allowlist) |
[Next: Built-in roles >](/Troubleshooting/Built-in-roles)
