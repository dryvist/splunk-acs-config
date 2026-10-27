# What to run

Pick the row for your task, set its parameters when you run the pipeline, and open its page for the steps.

| Task | Action | Parameters | Page |
| --- | --- | --- | --- |
| See differences | `plan` | `environment`: `all`, `nonprod` or `prod`. `types`: `all` or a `;` list of type names. `names`: `all` or a `;` list of names. `check`: `false` or `true`. | [Plan](/What-to-run/Plan) |
| Nightly drift check | `plan`, on a schedule | None. The schedule runs `environment` `all`, `types` `all` and `names` `all`, with `check` on. | [Plan](/What-to-run/Plan) |
| Read live into a pull request | `pull` | `environment`: `all`, `nonprod` or `prod`. `types`: `all` or a `;` list. `names`: `all` or a `;` list. | [Pull](/What-to-run/Pull) |
| Push one object | `push` | `environment`: `all`, `nonprod` or `prod`. `types`: one type name. `names`: one name or a `;` list. `delete`: `false`. | [Push](/What-to-run/Push) |
| Push a type | `push` | `environment`: `all`, `nonprod` or `prod`. `types`: one type name or a `;` list. `names`: `all`. `delete`: `false`. | [Push](/What-to-run/Push) |
| Copy nonprod to prod | `copy` on the command line, then `push` | Command: `copy nonprod prod`, with optional `--types`, `--names` and `--dir`. Then `push` with `environment`: `prod`. | [Copy nonprod to prod](/What-to-run/Copy-nonprod-to-prod) |
| Regenerate the README and apps.csv | `doc` on the command line | Command: `doc`, with optional `--dir`. | [Regenerate the README and apps.csv](/What-to-run/Regenerate-docs) |
| Delete live-only objects | `push` | `delete`: `true`. `environment`: `all`, `nonprod` or `prod`. `types` and `names`: the live-only objects. | [Delete live-only objects](/What-to-run/Delete-live-only-objects) |

Commands run on your machine. Their options are on [Commands](/Reference/Commands).
