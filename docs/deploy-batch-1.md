# Deploy runbook — Batch 1 (auth hardening)

This batch ships an IDOR fix, makes `user_id` NOT NULL on documents and conversations,
adds a JWT default-secret guardrail, and caches provider factories. Three of those four
changes are pure code — but the NOT NULL migration touches production data and the
guardrail can refuse to boot, so this runbook covers the safe order.

## TL;DR

1. Verify `JWT_SECRET_KEY` is set to a real value on Render. (Boot will fail otherwise.)
2. Count orphan rows on Neon. Decide: delete or reassign.
3. Stamp existing alembic state, then run the new migration.
4. Deploy.

---

## 1. Pre-flight: verify Render env

The guardrail in `app/config.py` refuses to construct `Settings` if `DEBUG=False`
**and** `JWT_SECRET_KEY` is the placeholder. If either of those is wrong on Render,
the next deploy crash-loops on startup.

Check the Render dashboard → docuchat-api → Environment. `JWT_SECRET_KEY` should be a
long random string, not the placeholder `change-me-in-production-...`. If you need
to (re)generate one:

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

Rotating the secret invalidates all currently-issued JWTs — users will need to log
in again. Acceptable for a portfolio app; coordinate if you have real users.

## 2. Count orphan rows on Neon

`a1b2c3d4e5f6_user_id_not_null.py` deletes rows where `user_id IS NULL` before
altering the column. Anything created before auth was added in Stage 6 is orphaned.
Chunks and messages cascade with their parent, so the blast radius is wider than
the row count suggests.

Run in the Neon SQL editor:

```sql
SELECT COUNT(*) AS orphan_docs FROM documents WHERE user_id IS NULL;
SELECT COUNT(*) AS orphan_convs FROM conversations WHERE user_id IS NULL;

-- If any orphan docs exist, this tells you how many chunks go with them:
SELECT COUNT(*) AS dependent_chunks
FROM chunks c JOIN documents d ON c.document_id = d.id
WHERE d.user_id IS NULL;
```

Three options if either count is non-zero:

- **Accept the delete.** Fine for a portfolio app — those rows were never visible to
  any user anyway (list endpoints filter by `user_id`).
- **Reassign to a real user.** If you want to keep the data, pick a user id and:
  ```sql
  UPDATE documents SET user_id = '<your-user-id>' WHERE user_id IS NULL;
  UPDATE conversations SET user_id = '<your-user-id>' WHERE user_id IS NULL;
  ```
  Then run the migration — the DELETE is now a no-op.
- **Snapshot first.** Use Neon's branch feature (Console → Branches → Create branch
  from main) to take a point-in-time copy before the migration, so you can roll back
  the data even if the schema migration succeeded.

## 3. Stamp alembic, then upgrade

The Neon schema was built by `Base.metadata.create_all()` on first boot, not by
running alembic migrations. So `alembic_version` is empty (or missing). A naïve
`alembic upgrade head` will try to re-create the `chunks` table that already exists
and fail.

Tell alembic the prior migrations are already applied, then run only the new one:

```bash
# From a Render shell (Dashboard → docuchat-api → Shell), with prod DATABASE_URL set
cd /opt/render/project/src/backend
alembic current                  # likely empty
alembic stamp 7f9546382ddb       # mark prior migrations as applied
alembic upgrade head             # runs only a1b2c3d4e5f6
alembic current                  # should now show a1b2c3d4e5f6 (head)
```

If you don't have shell access (free tier), the alternative is a one-off Render job
running the same three commands, or temporarily adding `alembic stamp 7f9546382ddb &&
alembic upgrade head` to the start command for a single deploy and then removing it.

## 4. Deploy the branch

Once the migration is applied, push/merge `chore/auth-hardening`. Render auto-deploys.
Confirm in the logs:

- No `ValidationError: JWT_SECRET_KEY is set to the placeholder` on startup.
- `/api/health` returns 200.
- A test chat works.

## Rollback

If something breaks after deploy:

```bash
# Code: revert the merge commit on main and push.
# DB: downgrade the migration (re-allows NULL user_id).
alembic downgrade 7f9546382ddb
```

The downgrade only restores nullability — it does **not** resurrect deleted orphan
rows. If you need those back, restore from the Neon branch snapshot you took in step 2.

## What this batch does NOT include

- No change to storage (Cloudflare R2 untouched).
- No change to the frontend.
- No change to the LLM/embedding providers.
- No new env vars required beyond ensuring `JWT_SECRET_KEY` is non-default.
