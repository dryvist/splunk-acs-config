# Regenerate the README and apps.csv

The doc command regenerates `README.md` and `apps.csv` in the config repo, and it is not a pipeline action.

`apps.csv` is written beside `README.md`. List cells in its `read` and `write` columns use `;`. Place it in an app's
`lookups/` folder and query it with `| inputlookup apps.csv`.

## Steps

1. Open a terminal in a local clone of the config repo.
2. Run `python acs_config.py doc`.
3. Review the changed `README.md` and `apps.csv` in the diff.
4. Merge the change to `main` through a pull request. Follow the merge steps on [Pull](/What-to-run/Pull).

## Verify

1. Confirm `apps.csv` is beside `README.md` in the config repo.
