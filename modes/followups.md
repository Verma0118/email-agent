# Mode: followups and sweep

## followups
Trigger: "follow-ups", "who should I nudge".
1. Run sync first if the last sync is more than 3 days old.
2. `tools/crm_tool.py followups`. Show the table and draft only for the rows the user picks. Show warm `replied` people first; they are the highest value.
3. Fetch the original sent email (`get_thread`). **Every claim about the sender must come from that email.** Add ONE new angle that is about *them* (verified recent news, a hook). A bare bump fails.
4. Follow the `follow_up` rules in `rules/email-types.md` (stay in thread, 50-75 words). Run the `email-reviewer` with the original email included.
5. After approval and the Gmail draft is created (reply in thread): `tools/crm_tool.py log-followup <id> --draft-id <id>`. The tool refuses a third follow-up. Two follow-ups and still silent means sweep.

## sweep (retire dead threads)
Trigger: "sweep", "clean up", or the brief shows active threads quiet 45+ days.
1. **Sync first** (a reply hiding in the inbox must not get swept).
2. `tools/crm_tool.py stale [--days N]`. Show the table.
3. Ask: `all` / `select 1,3-7` / `skip`. Also ask whether any of them deserve one fresh re-engagement email instead.
4. Approved rows: apply with `{"state": "dead", "status": "no_response", "signal": "stale sweep"}`.
Dead contacts stay in the archive for dedupe. Nothing is ever deleted.
