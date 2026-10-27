# Grant repository permissions

One time. Done at setup; you should not need this again.

This page grants the pipeline's build identity Contribute, Create branch and Contribute to pull requests on the config repo.

## Steps

1. Select **Project settings → Repositories**.
2. Select the `<config-repo>` repository.
3. Select **Security**.
4. Search for `<project> Build Service (<org>)`.
5. Select the identity.
6. Set **Contribute** to **Allow**.
7. Set **Create branch** to **Allow**.
8. Set **Contribute to pull requests** to **Allow**.

## Verify

1. Confirm **Contribute** shows **Allow** for the identity.
2. Confirm **Create branch** shows **Allow** for the identity.
3. Confirm **Contribute to pull requests** shows **Allow** for the identity.

If the pull step returns HTTP 403, see [Pull request permission](/Troubleshooting/Pull-request-permission).
