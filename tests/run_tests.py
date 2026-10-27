#!/usr/bin/env python3
"""Runs lint_draft.py on every fixture (works on Mac, Linux, and Windows).
Fixture name: <pass|fail>__<type>__<what>.txt
Uses tests/profile.test.json (fictional sender) so results never depend on a real profile."""
import subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LINT = HERE.parent / "tools" / "lint_draft.py"
subprocess.run([sys.executable, str(HERE / "make_fixtures.py")], check=True, capture_output=True)

ok = bad = 0
for f in sorted((HERE / "fixtures").glob("*.txt")):
    expect, typ, _ = f.stem.split("__", 2)
    r = subprocess.run([sys.executable, str(LINT), str(f), "--type", typ,
                        "--profile", str(HERE / "profile.test.json")],
                       capture_output=True, text=True, encoding="utf-8")
    if (expect == "pass" and r.returncode == 0) or (expect == "fail" and r.returncode == 1):
        ok += 1
        why = next((l[6:] for l in r.stdout.splitlines() if l.startswith("FAIL")), "")
        print(f"ok    {f.stem}" + (f"   <- {why}" if why else ""))
    else:
        bad += 1
        print(f"WRONG {f.stem} (expected {expect}, exit {r.returncode})")
        print("\n".join("      " + l for l in r.stdout.splitlines()))
print("---")
print(f"{ok} passed, {bad} wrong")
sys.exit(1 if bad else 0)
