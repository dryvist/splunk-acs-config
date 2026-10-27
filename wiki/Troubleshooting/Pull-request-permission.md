# Pull request permission

This page fixes HTTP 403 errors when the pull step publishes a pull request.

## Symptom

The pipeline's pull request step receives HTTP 403 after pushing its `acs-pull` branch.

## Cause

The identity `<project>` Build Service (`<org>`) lacks Contribute to pull requests on the config repo.

## Action

1. Grant that identity Contribute to pull requests on the config repo. See
   [Grant repository permissions](/Setup/Grant-repository-permissions).
2. Rerun the pull action. See [Pull](/What-to-run/Pull).

## Verify

The rerun creates a pull request targeting the repo's `main` branch.
