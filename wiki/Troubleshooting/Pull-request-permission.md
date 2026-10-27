# Pull request permission

[Home](/Home) > [Troubleshooting](/Troubleshooting) > Pull request permission

[[_TOC_]]

This page fixes permission errors when publishing a pull request.

## Symptom

The pipeline's pull request step receives HTTP 403 after pushing its
acs-pull branch.

## Cause

The identity `<project>` Build Service (`<org>`) lacks Contribute to
pull requests on the private config repo.

## Action

Grant that identity Contribute to pull requests on the private config repo,
then rerun the pull action.

## Verify

The rerun creates a pull request targeting the repo's main branch.

## Related

- [Repository permissions](/Getting-started/Grant-repository-permissions)
- [Pull environments](/Getting-started/Pull-environments)

---

[< Previous: Built-in roles](/Troubleshooting/Built-in-roles) |
[Next: Only live objects >](/Troubleshooting/Only-live-objects)
