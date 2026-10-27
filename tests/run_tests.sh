#!/bin/bash
# Runs the self-test (see run_tests.py).
exec python3 "$(dirname "$0")/run_tests.py"
