#!/usr/bin/env python3
"""Hard-fail checker for email-agent drafts. Mechanical rules only; the
email-reviewer agent still judges hooks, warmth, and truth.

Draft file format:
    Subject: <subject line>
    <blank line>
    <body, plain text or HTML>

Usage:
    lint_draft.py DRAFT --type coffee_chat|follow_up|reply|<personal type>
                  [--profile profile.json] [--their-words N]
Exit 0 = PASS (warnings allowed), 1 = FAIL, 2 = usage error.

Types come from TYPES below plus optional personal/lint.json (same schema).
"""
import argparse
import html
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # Windows consoles default to cp1252

SKILL = Path(__file__).resolve().parent.parent

# Shared types. Schema: min/max body words, subject (regex, {name}/{school_short}
# filled from profile), greeting (bang | hi | comma | bang_or_generic | any),
# cta (Calendar Invite required), signature (profile name + email required),
# required / banned (extra phrases, case-insensitive).
TYPES = {
    "coffee_chat": {"min": 140, "max": 160,
                    "subject": r"^{school_short} Student \| Coffee Chat Request \| [^|]+ \| {name}$",
                    "greeting": "bang", "cta": True, "signature": True},
    "follow_up": {"min": 50, "max": 100, "warn_over": 75, "subject": r"^Re: .+",
                  "greeting": "hi", "cta": False, "signature": False},
    "reply": {"min": 1, "max": 400, "subject": r"^Re: .+",
              "greeting": "hi", "cta": False, "signature": False},
}

BANNED = [
    "leverage", "caught my eye", "caught my attention", "piqued my interest", "as a signal",
    "couldn't help but notice", "could not help but notice", "i was struck by", "reach out",
    "reaching out", "finds you well", "i hope all is well", "vast range of knowledge",
    "extensive background", "deep expertise", "thought leader", "passionate about",
    "excited to", "would love to", "delve", "unpack", "deep dive", "at the intersection of",
    "i serve as", "what draws me to", "i look forward to connecting", "trajectory",
    "full-cycle ownership", "ethos", "systems-level", "p.s.", "alignment",
]
WARN_WORDS = ["pivot", "navigate", "align", "drive", "explore", "breadth", "magnitude", "scope"]

CONTRACTION = re.compile(
    r"\b\w+n['’]t\b|\b\w+['’](m|re|ve|ll|d)\b|\b(it|that|there|what|here|let|he|she|who|where|how)['’]s\b",
    re.I)
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿]")
DESCRIBES_DOCS = re.compile(
    r"\b(portfolio|resume)\b[^.!?]{0,40}\b(showcas|highlight|featur|cover|includ|demonstrat|contain)", re.I)


def load_types():
    types = dict(TYPES)
    extra = SKILL / "personal" / "lint.json"
    if extra.exists():
        types.update(json.loads(extra.read_text(encoding="utf-8")))
    return types


def to_text(body):
    body = re.sub(r"(?i)<br\s*/?>|</p>|</div>", "\n", body)
    body = re.sub(r"<[^>]+>", "", body)
    return html.unescape(body)


def split_draft(raw):
    lines = raw.strip("\n").splitlines()
    if not lines or not lines[0].lower().startswith("subject:"):
        return None, raw
    return lines[0].split(":", 1)[1].strip(), "\n".join(lines[1:]).strip("\n")


def split_signature(text):
    """Return (greeting, middle, signature). Signature starts at a line 'Best,'."""
    lines = [l.rstrip() for l in text.strip().splitlines()]
    sig_at = next((i for i, l in enumerate(lines) if l.strip().lower() in ("best,", "best")), len(lines))
    first = next((i for i, l in enumerate(lines) if l.strip()), 0)
    greeting = lines[first] if lines else ""
    return greeting, "\n".join(lines[first + 1:sig_at]), "\n".join(lines[sig_at:])


def sentences(text):
    flat = " ".join(text.split())
    return [s for s in re.split(r"(?<=[.!?])\s+", flat) if s]


def lint(raw, typ, spec, profile, their_words=None):
    fails, warns = [], []
    subject, body_raw = split_draft(raw)
    text = to_text(body_raw)
    greeting, middle, signature = split_signature(text)
    visible = f"{greeting}\n{middle}"

    # subject
    if subject is None:
        fails.append("no 'Subject:' first line")
    elif spec.get("subject"):
        pat = spec["subject"].format(name=re.escape(profile.get("name", "")),
                                     school_short=re.escape(profile.get("school_short", "")))
        if not re.match(pat, subject):
            fails.append(f"subject does not match the {typ} format: {subject!r}")
    if spec.get("subject_exact") and subject != spec["subject_exact"]:
        fails.append(f"subject must be exactly {spec['subject_exact']!r}")

    # greeting
    g = spec.get("greeting", "any")
    named = r"Good (Morning|Afternoon) [A-Z][\w.'’-]*( [A-Z][\w.'’-]*)?"
    ok = {
        "bang": re.fullmatch(named + "!", greeting.strip()),
        "comma": re.fullmatch(named + ",", greeting.strip()),
        "bang_or_generic": re.fullmatch(named + "!|Good (Morning|Afternoon)!", greeting.strip()),
        "hi": re.fullmatch(r"Hi [A-Z][\w.'’-]*[,!]", greeting.strip()),
        "any": True,
    }.get(g, True)
    if not ok:
        fails.append(f"greeting {greeting.strip()!r} is wrong for {typ} (expected style: {g})")
    if re.match(r"(?i)hi\b", greeting.strip()) and g in ("bang", "comma", "bang_or_generic"):
        fails.append("first-touch email must open 'Good Morning/Afternoon', never 'Hi'")

    # punctuation and format
    if "—" in text:
        fails.append("em dash (—) found")
    if re.search(r"\s[-–]\s", visible):
        fails.append("hyphen/en dash used as a clause connector ( - )")
    if ";" in visible:
        fails.append("semicolon found")
    for m in CONTRACTION.finditer(visible):
        fails.append(f"contraction: {m.group(0)!r}")
    if re.search(r"(?m)^\s*([-*•]|\d+\.)\s+", middle):
        fails.append("bullet or numbered list in body")
    if re.search(r"\*\*|<b>|<strong>", body_raw, re.I):
        fails.append("bold text in body")
    if EMOJI.search(visible) or (subject and EMOJI.search(subject)):
        fails.append("emoji found")
    if re.search(r"https?://", visible):
        fails.append("bare URL in visible text (use an <a href> with the display form)")
    if DESCRIBES_DOCS.search(visible):
        fails.append(f"describes resume/portfolio contents: {DESCRIBES_DOCS.search(visible).group(0)!r}")

    # banned language
    low = visible.lower()
    for phrase in BANNED + [b.lower() for b in spec.get("banned", [])]:
        if re.search(r"(?<!\w)" + re.escape(phrase) + r"(?!\w)", low):
            fails.append(f"banned phrase: {phrase!r}")
    for w in WARN_WORDS:
        if re.search(rf"\b{w}\w*\b", low):
            warns.append(f"check usage of {w!r} (banned when metaphorical)")
    for req in spec.get("required", []):
        if req.lower() not in " ".join(low.split()):
            fails.append(f"missing required line: {req!r}")

    # "I" streak
    streak = best = 0
    for s in sentences(middle):
        streak = streak + 1 if re.match(r"I\b", s) else 0
        best = max(best, streak)
    if best > 2:
        fails.append(f"{best} consecutive sentences start with 'I' (max 2)")

    # CTA
    if re.search(r"\bzoom\b", low):
        fails.append("mentions Zoom; the CTA is a Calendar Invite")
    if spec.get("cta") and "calendar invite" not in low:
        fails.append("missing CTA: 'Calendar Invite'")

    # signature
    if spec.get("signature"):
        for key in ("name", "sending_email"):
            val = profile.get(key)
            if val and val not in signature:
                fails.append(f"signature missing profile {key} {val!r}")
        if not signature:
            fails.append("no signature block (starts with 'Best,')")

    # length
    words = len(re.findall(r"[A-Za-z0-9][\w'’.-]*", middle))
    lo, hi = spec.get("min", 0), spec.get("max", 10**6)
    if their_words and typ == "reply":
        lo, hi = int(their_words * 0.8), int(their_words * 1.2) + 1
    if not lo <= words <= hi:
        fails.append(f"body is {words} words; {typ} needs {lo}-{hi}")
    elif spec.get("warn_over") and words > spec["warn_over"]:
        warns.append(f"body is {words} words; target is under {spec['warn_over']}")
    return fails, warns, words


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("draft")
    ap.add_argument("--type", required=True)
    ap.add_argument("--profile", default=str(SKILL / "profile.json"))
    ap.add_argument("--their-words", type=int, help="reply only: word count of their message")
    a = ap.parse_args()

    types = load_types()
    if a.type not in types:
        print(f"unknown type {a.type!r}; known: {', '.join(sorted(types))}")
        return 2
    prof_path = Path(a.profile).expanduser()
    if not prof_path.exists():
        print(f"no profile at {prof_path}; run the email-agent once to create it")
        return 2
    profile = json.loads(prof_path.read_text(encoding="utf-8"))
    fails, warns, words = lint(Path(a.draft).read_text(encoding="utf-8"), a.type, types[a.type], profile, a.their_words)
    for f in fails:
        print(f"FAIL  {f}")
    for w in warns:
        print(f"WARN  {w}")
    print(f"RESULT: {'FAIL' if fails else 'PASS'} ({a.type}, {words} words, "
          f"{len(fails)} fail, {len(warns)} warn)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
