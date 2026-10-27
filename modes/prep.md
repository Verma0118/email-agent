# Mode: prep (call is booked)

Trigger: "prep me for [name]", a call on the `calendar_id` calendar within 48h, or a reply that locks a time.
For **job interviews** on a tracked application, use `modes/jobs.md` and run `/interview` instead.

1. Load: the CRM row (master `relationship` + `call_evidence`, or the archive row), the full Gmail thread (what the sender claimed, what they said), the research brief in `<notes_dir>/Research/` if it exists, `claims_sources` from `profile.json`, and anything `personal/README.md` says to load.
2. Re-research the person and company. **Verify before use:** every company fact in the pack is confirmed on the official site or a primary source. A snippet is only a lead.
3. Build the pack:
   - **Their angle:** role, path, what they probably care about (public information only)
   - **3 verified conversation hooks** (recent and specific)
   - **Consistency brief:** every claim the sender made in the thread. No claim on the call that is not already on paper.
   - **30-second intro** tailored to them, grounded in claims_sources
   - **6-8 questions to ask.** Cut any the research already answers.
   - **Gaps with honest bridges:** acknowledge, point to an adjacent project, say what they are learning
   - **The ask to close with** (referral, next person to talk to, internship timeline)
   - Plain language: no jargon they would have to fake
4. Show it in chat. If `notes_dir` is set, save to `<notes_dir>/Prep/<YYYY-MM-DD>_<Name>.md`. Offer a 10-minute mock call where you play the contact.
5. After the call: draft the thank-you note (approval-gated). If the person is still in the archive, propose `promote` with manual call evidence (`{"source":"manual","id":"user-confirmed","date":...}`).
