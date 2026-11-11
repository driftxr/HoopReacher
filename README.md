# HoopReacher

Personal NBA standings picks with a static website at https://hoopreacher.com/.

## Automatic publishing

GitHub Actions runs the Python generator on pushes to main, manually from Actions, and at 00:17, 06:17, 12:17, and 18:17 UTC. Standings/rosters are cached for 12 hours; schedules, scores and averages for 6 hours. Scheduled jobs can be delayed. Set Settings → Pages → Source to GitHub Actions. No personal server is required.

A build must successfully retrieve all required NBA data before deployment. If NBA access fails from GitHub, the previous public website stays online; inspect the failed Actions run. Cache persistence is best-effort, so cache eviction can trigger an earlier refresh.

Only generated dist/ files are deployed. CNAME preserves the custom domain. Personal picks live in the visitor's browser and can be imported/exported; they are not stored in this repository.

## Local generation

Python 3.10+ required:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python export_static.py --output dist
```

Edit templates/, static/, and personalize.py; the next successful build publishes those changes. The existing root index.html is retained as the legacy site and is not the Actions deployment artifact.
