# Factual reconstruction

After preserving the original, the origin agent prepares a separate summary using the context still available. Use the [summary contract](../summary.schema.json) and [runtime](../runtime/README.md). Do not start Reflect, interview the user or wait for embeddings. Return to the active task if summary work fails; leave reconstruction pending.

Retain the request, scope, constraints, observable actions, results, user corrections and explicit authorizations, with sources. Keep author and order unknown when not evidenced. Separate supported expectations, causal hypotheses, contradictions and gaps. Authorization text is evidence for review, not a permission granted by this adapter.

Keep only necessary sanitized excerpts. Label quotations, paraphrases and record text accurately. Each claim cites selected sources and at least one retained excerpt. Credentials, unrelated conversations and full transcripts stay outside this artifact. A schema cannot prove sanitization or factual truth; the author must check both before saving.

Record pertinent instructions and skills with available versions, temporal role and evidence of exposure, availability, selection, reading or loading. A document consulted later does not prove it was loaded in the historical session. Claims about historical selection/read/load need retained message or runtime evidence. Unknown context stays unknown.

For a historical observation, use mode posthoc and state what remains inaccessible. Session retrieval is optional; do not invent a transcript. Record the author when available, preparation date, linked observations, previous summary revision and completeness. Null request, expectation or author must also appear in unknowns. Partial evidence produces a partial summary.

Corrections append another version. Preserve contradictions, prior summaries, originals and user decisions. Versions of one summary are not additional incidents. Later Reflect sessions can use the retained excerpts even if the origin session cannot be opened.
