# Create the private config repo

One time. Done at setup; you should not need this again.

This page creates the private repository that stores the TOML configuration, using the `example` folder of this tools repository.

## Steps

1. Select **Repos → Files**.
2. Select the repository selector.
3. Select **New repository**.
4. Select **Git** as the type.
5. Type `<config-repo>` in **Name**.
6. Select **Create**.
7. Select **Clone** on the new repository.
8. Copy the HTTPS clone URL as `<config-clone-url>`.
9. Open a terminal in a folder for local clones.
10. Run `git clone <tools-clone-url>`, using the clone URL of this tools repository.
11. Run `git clone <config-clone-url>`.
12. Run `cp -R splunk-acs-config/example/. <config-repo>/`.
13. Run `cd <config-repo>`.
14. Run `git branch -M main`.
15. Run `git add --all`.
16. Run `git commit -m "Add ACS configuration"`.
17. Run `git push origin main`.

## Verify

1. Confirm `azure-pipelines.yml`, `environments.toml` and `objects/` appear on `main` in **Repos → Files**.
2. Confirm `environments.toml` lists `nonprod` and `prod`.
3. Open `objects/` and confirm it lists one `.toml` file for each object type, for example `indexes.toml`.
