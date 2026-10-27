#!/usr/bin/env python3
"""Generate one failing fixture per hard rule by mutating the passing coffee_chat example."""
from pathlib import Path

HERE = Path(__file__).resolve().parent / "fixtures"
base = (HERE / "pass__coffee_chat__voice_example.txt").read_text(encoding="utf-8")

MUTATIONS = {
    "em_dash": ("I saw you moved from motorsport", "I saw you moved — quickly — from motorsport"),
    "contraction": ("I have attached my resume", "I've attached my resume"),
    "banned_phrase": ("I saw you moved from motorsport", "Your move from motorsport caught my eye, and I saw you moved from motorsport"),
    "wrong_subject": ("Subject: STATE Student | Coffee Chat Request | Northwind Aero | Alex Rivera",
                      "Subject: Quick question about battery packs"),
    "hi_greeting": ("Good Morning Dana!", "Hi Dana!"),
    "zoom_cta": ("send a Calendar Invite", "send a Zoom link"),
    "describes_portfolio": ("my portfolio is at alexrivera.dev", "my portfolio showcasing CAD and FEA work is at alexrivera.dev"),
    "bare_url": ("my portfolio is at alexrivera.dev", "my portfolio is at https://alexrivera.dev"),
    "wrong_sender_name": ("Best,\nAlex Rivera", "Best,\nSam Patel"),
    "too_long": ("works on every season.",
                 "works on every season. Our team spends most of the spring arguing about how to split work between pack design and thermal testing, so hearing how a real company handles that would help us a lot this year."),
    "three_I_sentences": ("I hope your week has been off to a good start! My name is Alex Rivera",
                          "I hope your week has been off to a good start! I am writing from State. I study engineering. I am Alex Rivera"),
    "semicolon": ("I am a Powertrain Lead on Formula Racing, a student team", "I am a Powertrain Lead on Formula Racing; a student team"),
}

for name, (old, new) in MUTATIONS.items():
    assert old in base, name
    (HERE / f"fail__coffee_chat__{name}.txt").write_text(base.replace(old, new, 1), encoding="utf-8")
print(f"wrote {len(MUTATIONS)} failing fixtures")
