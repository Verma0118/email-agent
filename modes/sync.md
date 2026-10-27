# Mode: sync (Gmail + Calendar -> CRM)

Trigger: "sync", "check replies", "update CRM", or the brief says the sync is stale. Also run sync before every sweep.
Uses Gmail and Calendar MCP. This mode is read-only against Gmail: never label, archive, trash, or send.

1. `tools/crm_tool.py sync-targets`. This gives master plus archive contacts in `active`/`replied`, and pre-batched queries.
2. Run each Gmail query (`search_threads`, `pageSize 50`, `view THREAD_VIEW_METADATA_ONLY`). If the output is too large, parse the saved file with python. Skip message ids that are already processed.
3. Calendar: `list_events` on the calendar in `profile.json` → `calendar_id` since last_sync. Match attendees to contact emails.
4. For candidate threads, run `get_thread` (MINIMAL, or PLAIN_TEXT when the wording matters). **Classify from message content, never from the subject alone.**

   | Signal | Proposed change |
   |---|---|
   | Found in Sent, contact `drafted` | status `no_reply`, `sent_at` = sent date |
   | Human reply, no call yet | archive state `replied`, status `replied` (flag it: needs a response) |
   | Call happened: past calendar event they did not decline, or a "great talking" / thank-you message after the call | **promote candidate** (needs the user's approval, uses `promote`) |
   | Call scheduled, nothing after | "Likely" list for the user to decide |
   | OOO / auto-reply | no change |
   | Bounce naming the address | status `bounced`, state `dead` |
   | Master contact: any new exchange | `last_contact` = date |
   | Redirect to someone else | status `replied`, note the new name for a fresh draft |

   No confident match goes in the Unmatched list. Never guess.
5. **Show one batch, write nothing yet:** a table (`# | Name | Company | Signal | Current -> Proposed | Source (date)`), then Promote candidates (with evidence), Likely calls, Unmatched, and a noise count.
6. Approved rows: write `[{id, status?, state?, signal, source, sent_at?, last_contact?, message_ids}]` and run `tools/crm_tool.py apply <file>`. For approved promotions, write `[{id, relationship, call_evidence:[{source,id,date}], last_contact}]` and run `tools/crm_tool.py promote <file>`.
7. Mark every scanned id processed, then close the run: `tools/crm_tool.py mark-processed <ids...> --finish`.
