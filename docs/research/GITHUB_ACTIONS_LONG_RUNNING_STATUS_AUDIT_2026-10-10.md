# GitHub Actions Long-Running Status Check — 2026-10-10

User reported that the TQQQ Dot-Com Survivability workflow appeared to run for 12+ hours. Checked GitHub's Actions Runs API and job records for the exact run IDs previously being monitored.

- [TQQQ Dot-Com Survivability Research #24 / run 37925744760](https://github.com/eklu654/Trading-Bot/actions/runs/37925744760): GitHub API reports `created_at=2026-10-09T11:45:54Z`, `run_started_at=2026-10-09T11:45:54Z`, and completed successfully at `2026-10-09T11:46:42Z` — elapsed wall time **48 seconds**. All 11 substantive steps succeeded, including all four research scripts and artifact upload.
- [research-tests #1625 / run 37925744590](https://github.com/eklu654/Trading-Bot/actions/runs/37925744590): created/started at `2026-10-09T11:45:53Z`, completed successfully at `2026-10-09T11:46:49Z` — elapsed wall time **56 seconds**. Dependency installation, pytest, and the event-attribution script all succeeded.
- Both runs used commit `37aa32278ca4a31de25ec751217c49d9c40b15d4`, event `push`, attempt 1.
- Current API state is `completed/success`, not queued or in progress. The recorded run timestamps do **not** support a 12-hour execution for these IDs.

Diagnosis: the exact runs checked are not the long-running job described; their recorded execution was under one minute. If the Actions page showed 12+ hours for one of these IDs, that conflicts with GitHub's current run and job records and is most consistent with a stale/incorrect UI state or a different run ID being viewed. Do not claim the precise UI cause is proven. If it recurs, record the full run ID/URL and compare it to the API timestamps before cancelling; these two runs need no cancellation or rerun.
