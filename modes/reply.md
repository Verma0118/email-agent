# Mode: reply (respond in a live thread)

Trigger: someone replied ("John answered", a `replied` contact in the brief, or a pasted thread).
1. `get_thread` (PLAIN_TEXT) and read the whole thread. Find the CRM row (`is-known`).
2. Work out the job: lock a time, answer a question, or confirm. Say it in one line.
3. Draft per `reply` in `rules/email-types.md`: match their length +/- 20%, first name, no signature block, no re-pitch, warm not transactional. All grammar rules still apply.
4. Proposing times? Check the `calendar_id` calendar for conflicts first (Calendar MCP). After the time is agreed, offer to create the invite. Never create it without asking.
5. After approval: `mcp__claude_ai_Gmail__create_draft` replying in the thread (not a new thread). Replies are exempt from send timing.
6. Log it with `apply` (`last_contact`, a note). When a call happens later, sync will propose `promote`.
