# ONLY LIVE objects

[Home](/Home) > [Troubleshooting](/Troubleshooting) > Only live objects

[[_TOC_]]

## Symptom

Plan reports ONLY LIVE for an object that is present in ACS but absent from
the repository.

## Action

Review the object, then choose one:

- Pull it into the repository to keep it managed.
- Push with the Delete live-only objects option (`--delete`) to remove it from
  ACS. Run plan first to confirm which objects will be removed.

A push without `--delete` does not remove the object. The push then fails with
`N differences remain after push`.

## Verify

Run plan again and confirm each ONLY LIVE line was pulled or removed as
intended.

## Related

- [Commands](/Reference/Commands)
- [Object types](/Reference/Object-types)

---

[< Previous: Pull request permission](/Troubleshooting/Pull-request-permission)
