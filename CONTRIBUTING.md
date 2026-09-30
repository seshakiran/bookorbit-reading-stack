# Contributing

Start with `docs/SPEC.md`. Keep current behavior distinct from planned features, and report which host/device/version you tested.

Before a pull request:

```sh
python3 scripts/check_public_tree.py
python3 scripts/validate.py
```

The public-tree check uses `git ls-files` in a checkout, including staged additions; stage only reviewed source and documentation. It is a guardrail, not a substitute for manual review or a dedicated secret scanner.

Do not commit runtime configuration, authentication packages, database dumps, books, fonts, private addresses, or unredacted logs. Reproduce a bug with a public-domain fixture where possible. Never include a personalized BookOrbit plugin ZIP.

Deployment changes should document their effect on existing data and be exercised in a disposable environment. Do not test installers against an active personal library. Native service labels and ports are fixed; a second installation can interfere with the first.
