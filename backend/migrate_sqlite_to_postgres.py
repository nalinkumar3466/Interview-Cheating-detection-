"""
This repository no longer supports a local SQLite database.

The previous helper script `migrate_sqlite_to_postgres.py` has been retained
only as a placeholder, but the project now requires a Postgres `DATABASE_URL`.

If you still have a local `berribot.db` and need to migrate it, please restore
this script from your VCS history or use a DB migration tool. Otherwise, set
`DATABASE_URL` (or create `backend/.env.postgres`) and run your app.
"""
import sys

print("migrate_sqlite_to_postgres.py is deprecated: project no longer uses SQLite.")
print("If you need to migrate data, restore the original script from git history.")
sys.exit(0)
