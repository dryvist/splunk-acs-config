# ACS authentication

[Home](/Home) > [Troubleshooting](/Troubleshooting) > Authentication

[[_TOC_]]

This page troubleshoots failed ACS authentication and authorization.

## HTTP 401

Check that the ACS token is valid and intended for the ACS audience. Confirm
the variable group defines `ACS_TOKEN`. The pipeline passes it to the tool as
`STACK_TOKEN`.

## HTTP 403

Confirm the token user has the sc_admin role. Check that the token belongs to
the selected stack and that the stack name is correct.

Do not put a token value in a config file, pipeline log, or pull request.

## Related

- [Configure access](/Getting-started/Configure-access)
- [ACS allowlist](/Troubleshooting/ACS-allowlist)
- [Commands](/Reference/Commands)

---

[Next: ACS allowlist >](/Troubleshooting/ACS-allowlist)
