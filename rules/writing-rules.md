# Writing Rules (single source of truth)

Applies to every email the agent drafts. Read before drafting, scan before showing.
Per-type subjects, lengths, and structure: `email-types.md`. Voice and examples: `voice.md`.
Precedence when files disagree: **`personal/` (if present) > this file > email-types.md > voice.md**.

"The sender" = the person in `profile.json`. Every `{field}` below is filled from that file. Never use another person's details.

---

## 1. Who the sender is (use only what is true)

Name, school, year, major, minor: from `profile.json`.
Involvements: `profile.json` → `involvements`. Pick 1-2 whose `use_for` matches the target. Describe each with its `clause`, never just the title.
**Verify every claim** (involvement, project, skill, metric) against `claims_sources` before citing it. Not found there = do not write it. Never embellish.

---

## 2. Grammar and format: hard fails (scan every draft; `tools/lint_draft.py` checks most of these)

- **No em dashes (—)** anywhere in the body. Rewrite the sentence.
- **No hyphen as a clause connector** ( - between clauses).
- **No semicolons** standing in for dashes.
- **No contractions.** "I am", "I would", "I have", "it is", "that is", "you are".
- **No more than 2 consecutive sentences starting with "I".**
- **One CTA only**: Calendar Invite (not "Zoom link").
- **No bullet points and no bold** inside the email body.
- No "P.S." unless the sender asks. No three-plus adjectives describing themself.
- No all-caps, no emojis (body or subject).

### Greeting and opener
- First touch: `Good Morning [Name]!` before noon, `Good Afternoon [Name]!` from noon. Never `Hi [Name]!` on first touch.
- One short warm line right after, varied across emails:
  - "I hope your week has been off to a good start!"
  - "I hope you are having a good week!"
  - "Hope your week is going well!"
- Never: "I hope all is well", "I hope this email finds you well", or repeating the time of day.

### Links and attachments
- HTML body. Links are `<a href="...">` anchors whose visible text is the display form (`portfolio_display`, `linkedin_display`). Never paste a bare URL; Gmail wraps it in a tracking redirect.
- **Never describe what the resume or portfolio contains.** Approved line: "I have attached my resume, and my portfolio is at {portfolio_display}." No portfolio in the profile: "I have attached my resume for your reference."

### Signature
```
Best,
{name}
{degree_line}
{linkedin_display}
{phone} | {sending_email}
```
Skip the phone if the profile has none.

---

## 3. Banned words and phrases

Verb-as-noun / metaphor: leverage, pivot (noun), navigate (metaphorical), align / alignment, drive (as metaphor).

Observation phrases no human says: "caught my eye", "caught my attention", "piqued my interest", "[X] as a signal", "I couldn't help but notice", "I was struck by".

Filler openers: "I wanted to reach out", "I am reaching out because", "reach out" (anywhere), "I hope this email finds you well", "I hope all is well", "Good [time], I hope...".

Corporate-speak: "vast range of knowledge", "extensive background", "deep expertise", "thought leader", "passionate about", "excited to", "would love to", "delve into", "unpack", "explore" (careers/ideas), "deep dive", "at the intersection of", "where X meets Y".

Unnatural constructions: "I serve as [role]" (write "I am"), "What draws me to [company]" (write "What I like about").

Too sophisticated for a student: breadth, trajectory, full-cycle ownership, ethos, magnitude / scope (abstract), systems-level problems. Rule: if it sounds odd said out loud by a college student, cut it.

Endings: "Feel free to reach out", "I look forward to connecting" (use "I look forward to hearing from you"). "Thank you for your time and consideration" at most once.

Structure tells: perfectly parallel sentences, perfectly balanced compound sentences, long comma chains.

---

## 4. Hook quality (the most important field)

- One real, citable fact about the person, phrased the way a person talks, tied to why the sender is writing.
- Pattern: "I saw [specific fact] and [natural follow-up]."
- **Warmth test:** remove the recipient's name. If the sentence could go to anyone else at the company, rewrite.
- Every hook traces to a fetched page or primary source, not a search snippet. Record the source URL in the research brief.
- No real hook after research: tell the sender before drafting. Never ship a generic email.

---

## 5. Who to email (confidence bar)

- Role must be **clearly current** on the profile. Ambiguous tense: do not draft; list it for the sender to review or DM.
- Email must have format evidence (documented pattern, public example, or Hunter `verification: valid`). A Hunter score alone is a guess.
- **Hunter nickname retry:** if the full first name fails, retry with the common short form (Christopher/Chris, Anthony/Tony, Matthew/Matt, Robert/Rob, William/Will, Michael/Mike) before saying no email exists.
- New domain: `dig +short MX <domain>` first. No MX = cannot receive mail.
- **Dedupe before drafting:** `tools/crm_tool.py is-known <email>`. Known contact = never cold-email again; use follow-up or reply rules.

---

## 6. CC rules

None by default. `personal/` may add CC rules for specific tracks; record any CC in the CRM `cc` field.

---

## 7. Approval and send timing

- **Never push to Gmail without explicit approval.** Draft in chat, iterate, ask "Approve to push to Gmail?". "Dump them in drafts" is not approval of content.
- One Gmail draft per contact: get wording final before pushing (re-pushes leave duplicates).
- **Never send.** The pipeline ends at "Draft created. Check Gmail Drafts."
- **Send timing** (when `schedule_after_noon` is true): new outreach and cold follow-up bumps drafted after 12:00pm local are tagged "schedule-send tomorrow 8am". Replies in live threads are exempt.

---

## 8. Pre-show checklist

```
[ ] tools/lint_draft.py: PASS
[ ] Subject exactly matches email-types.md for this type
[ ] Hook specific, sourced, passes warmth test
[ ] Involvement matched to target, verified in claims_sources
[ ] Links are <a href> anchors, no bare URLs
[ ] CC rule applied (personal tracks only)
[ ] Email verified (Hunter valid / format evidence / MX) and is-known checked
[ ] After-noon new outreach tagged schedule-send 8am
[ ] email-reviewer verdict applied
```
