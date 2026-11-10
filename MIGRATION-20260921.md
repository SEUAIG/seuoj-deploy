# Historical OJ data restoration (2026-09-21)

Source files supplied by the operator:

- `backup-mysql.sql` (full MySQL dump, including the `mysql` system schema)
- `backup-files.tar.gz` (application data)
- `backup-config.tar.gz` (previous configuration and secrets)

All three originals are staged on the server in
`/home/user/oj-restore-staging-20260921` (directory mode 700, originals mode
600). SHA-256 values were checked against the local files before import.

## Restoration decisions

- The `mysql` system schema from the old server was excluded. Only the
  `seuoj` application schema was imported.
- A scratch `seuoj_restore_test` schema was imported first. It has the same
  27 tables and column definitions as the new deployment. It was removed
  after the live restore passed verification.
- Before changing the live database, it was exported to
  `current-seuoj-before-restore.sql` in the staging directory. Existing
  backend, judge and agent data were archived to
  `current-runtime-before-restore.tar.gz` there.
- The historical `data/judgend`, `data/backend` and `data/agent` directories
  were restored. The old `data/init` and `backup-config.tar.gz` were *not*
  applied: doing so would overwrite the new deployment's secrets and proxy
  configuration. The old configuration archive remains staged for reference.
- The current deployment's superadmin password hash was preserved. Its
  password remains the one stored on the operator's Windows PC in
  `C:\Users\asus\.ssh\seuoj-admin-password.txt`.

## Verification

| Data | Restored count |
| --- | ---: |
| Users | 268 |
| Problems (including hidden/deleted rows) | 141 |
| Submissions | 6,392 |
| Contests | 9 |

The frontend, backend, judge and database containers are running. The
administrator login, public problem page, historical submission detail and a
C++20 online judge run against restored problem `P0001` were verified.

The service is still HTTP-only. The restored data contains real historical
accounts and submissions. Port 2280 was initially bound to loopback after
restoration, then reopened to the campus network at the operator's request.
Configure HTTPS before broader testing or production use.
