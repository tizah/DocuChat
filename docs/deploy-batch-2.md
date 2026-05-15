# Deploy runbook — Batch 2 (async resilience)

Three changes, all code-only. No migration, no env vars, no destructive
operations. Deploy is a regular push-to-merge.

## What ships

- **Embedder goes async.** `OpenAIEmbeddingProvider.embed` and `embed_query` now
  wrap the sync OpenAI client in `asyncio.to_thread`. Callers in
  `pipeline.py` and `rag.py` `await` them. The event loop is no longer blocked
  for the duration of an embedding call (~50ms–2s depending on batch size).
- **LLM streaming goes async.** `OpenAILLMProvider` and `AnthropicLLMProvider`
  now use `AsyncOpenAI` / `AsyncAnthropic`. `stream_chat` is an `async`
  generator. `rag.py::stream_rag_response` and `chat.py::event_generator`
  updated to `async for`. Token streaming no longer blocks the event loop
  between tokens — concurrent chats can interleave properly.
- **Startup reconciliation.** On lifespan startup, any documents in
  `processing/extracting/chunking/embedding` are flipped to `failed` with
  message "Processing was interrupted (server restart). Re-upload to retry."
  Free-tier Render dynos spin down regularly; without this, a doc whose
  pipeline was mid-flight at spin-down hangs forever on the UI's polling
  spinner.

## Why it matters in prod

Render's free tier runs a single worker on a single CPU. Without the async
changes, every embedding call and every token of LLM streaming blocked every
other request — including health checks. Under any concurrency at all, p99
latency degrades sharply. After this change, the event loop stays responsive
through both phases.

The reconciliation pass is a 10-line lifespan hook but covers a real failure
mode you'll hit weekly on the free tier: dyno sleeps mid-pipeline, comes back
without the in-memory `asyncio.Task`, and the doc row sits at `embedding`
forever.

## Deploy

```bash
git push origin chore/batch-2-async-resilience  # already done
gh pr merge --squash <PR#>                       # after review
# Render auto-deploys on push to main
```

## Smoke checks after deploy

1. `/api/health` returns 200.
2. Upload a small PDF → it should reach `ready` within a few seconds.
3. Chat against it → tokens stream visibly (not in one big chunk at the end).
4. Render logs should NOT contain `Reconciled N stuck document(s)` unless a
   prior deploy genuinely left one stuck. If you see it, that's working as
   intended — the corresponding doc row will be `failed` with the explanatory
   message and the user can re-upload.

## Rollback

Pure code change — `git revert <merge-sha>` on main and push. No DB state to undo.

## What this batch does NOT include

- No change to the embedding model or vector dimensions.
- No retry logic added beyond what was already there (tenacity on `_call_api`).
- No streaming-side error recovery (token stream still aborts on provider error).
- Reconciliation only fires on **startup**, not on a heartbeat — if the dyno
  stays alive but the background task dies, the doc still hangs until the next
  restart. That's a follow-up if it becomes a real problem.
