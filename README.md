# Email Agent

A Claude Code agent for students: cold coffee-chat outreach plus a full job search pipeline.

- **Outreach:** researches a person, drafts the email in a fixed format, checks it against the rules, and saves a Gmail draft only after you approve it. **It never sends anything.** It tracks who you emailed, nudges follow-ups, and preps you for calls.
- **Jobs:** sets up your job profile from your resume, searches job boards, ranks postings against your profile, tailors your CV and cover letter, tracks applications, and preps you for interviews (built on [ai-job-search](https://github.com/MadsLorentzen/ai-job-search)).

## Install (Mac, no GitHub account needed)
1. Install [Claude Code](https://claude.com/claude-code) and sign in (Claude Pro or higher).
2. In Terminal:
   ```bash
   curl -fsSL https://raw.githubusercontent.com/Verma0118/email-agent/main/get.sh | bash
   ```
   It asks whether to set up job search too. Say yes if you want it.
3. Type `email-agent`. The first run asks for your details (name, school, clubs, resume) and writes `profile.json`, then offers to set up your job profile.
4. Optional but recommended: in claude.ai → Settings → Connectors, connect **Gmail** and **Google Calendar** so drafts land in Gmail and replies are tracked.

Update any time by running the same `curl` line again. Your `profile.json` and `personal/` folder are kept.

## Use
Type `email-agent`, then say what you want:
- Paste a LinkedIn URL, or "email Jane Doe at Company": drafts a coffee chat (cold, warm intro, or after applying).
- "sync": checks Gmail and Calendar for replies and calls (shows changes and asks before saving).
- "follow-ups": lists people to nudge (max 2 nudges each).
- "prep me for Jane": builds a call prep sheet.
- "find jobs", "rank", "apply to <link>", "tailor my CV", "cover letter", "interview prep for <company>".

## Files
- `rules/`: grammar, banned words, subject lines, word counts, voice examples. Edit these to change the style.
- `modes/`: step-by-step procedures for each mode.
- `tools/crm_tool.py`: contact tracker (`{crm_dir}/contacts.json` + `contacts_archive.json`), with backups.
- `tools/lint_draft.py`: checks a draft for hard-rule breaks. Run `tests/run_tests.sh` to self-test.
- `profile.json` (yours, never committed): who is sending. See `profile.example.json`.
- `personal/` (optional, yours, never committed): extra email tracks or overrides just for you.

Your contacts live in `~/EmailCRM` and your job profile in `~/ai-job-search`, both on your own computer only. Do not push either to a public repo.
