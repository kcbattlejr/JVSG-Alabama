#!/usr/bin/env bash
set -euo pipefail
VENV="$HOME/.venvs/jvsg"
python -c 'import ssl; print("Python TLS support:", ssl.OPENSSL_VERSION)'
python -m venv "$VENV"
"$VENV/bin/python" -m pip install --disable-pip-version-check -e '.[dev,data]'
"$VENV/bin/python" -m pip check
printf 'JVSG environment ready. Interpreter: %s/bin/python\n' "$VENV"
