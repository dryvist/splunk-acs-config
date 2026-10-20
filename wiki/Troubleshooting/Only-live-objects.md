# ONLY LIVE objects

[Home](/Home) > [Troubleshooting](/Troubleshooting) > Only live objects

[[_TOC_]]

## Symptom

Plan reports ONLY LIVE for an object that is present in ACS but absent from
the repository.

## Action

Review the object and decide whether to pull it into the repository or remove
it from ACS. Keep the default push behavior when the object should remain
unmanaged.

Use push --delete only after the plan confirms which live-only objects will be
removed.

## Verify

Run plan again and confirm every ONLY LIVE line has an intentional outcome.

## Related

- [Commands](/Reference/Commands)
- [Object types](/Reference/Object-types)

---

[< Previous: Pull request permission](/Troubleshooting/Pull-request-permission)
