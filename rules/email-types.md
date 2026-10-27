# Email Types (single source of truth for subjects, length, structure)

Three shared types. Grammar and hard rules: `writing-rules.md`. Voice and examples: `voice.md`.
`personal/` may add more tracks for one user; those never apply to anyone else.

## Classify first (state it before drafting)

```
is-known says contact exists?
  status replied / call_done, sender responding  -> reply
  sent, no reply, 7+ days, follow_up_count < 2   -> follow_up
  otherwise                                      -> stop, ask (never cold-email a known contact)
new contact:
  personal track applies (see personal/)         -> that track
  else                                           -> coffee_chat, pick variant:
      already applied to a role there            -> applied
      mutual connection / referral / alum        -> warm
      else                                       -> cold
```
Say it: "Classifying as: coffee_chat (warm)".

## Subjects (fixed; never freelance)

| Type | Subject |
|---|---|
| coffee_chat (all variants) | `{school_short} Student \| Coffee Chat Request \| [Company] \| {name}` |
| follow_up | `Re: [original subject]` (stay in thread) |
| reply | `Re: [original subject]` (stay in thread) |

Never: per-person "Quick question about..." subjects, "Following up on my message", "Important: ...", "[Name], thought you might find this interesting".

## coffee_chat: **140-160 words body**

Same subject, length, and skeleton for all three variants. Only sentence 2 changes.
1. `Good Morning/Afternoon [Name]!` + one warm line
2. One sentence: name, year at school, major, why writing.
   - cold: nothing extra
   - warm: name the connection in one clause ("Jordan Park mentioned you...")
   - applied: name the role they applied to ("I recently applied for the Summer 2027 Structures Intern role")
3. One sentence: the 1-2 matched involvements, each with its clause
4. One or two sentences: the hook, and why this company (specific, not homepage flattery)
5. Ask: 20-30 minutes, happy to work around their schedule and send a Calendar Invite
6. Resume/portfolio line from writing-rules section 2
7. Signature

## follow_up: **50-75 words (max 100)**
- In thread, no warm opener, "Hi [Name]," if they ever replied
- "in case it got buried" style reference, plus ONE new angle about *them*
- Claims about the sender only from the original email (no new claims)
- Ask: 20 minutes this week or next
- Max 2 follow-ups per contact, ever (`crm_tool.py log-followup` enforces)

## reply: **match their length +/- 20%**
- First name only; sign off "Best," + first name, no signature block
- One job: lock the meeting, answer the question, or confirm the time. No re-pitch.
- Warm, not transactional: an exclamation mark on the eager line ("Friday at 1:00 ET works great for me!"), close with "Looking forward to it!". No over-thanking.
- Invite phrasing: "I have sent a calendar invite for that time as well to lock it in." Never "I will send one shortly."
