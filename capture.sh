#!/usr/bin/env bash
# Capture the local environment into committable files.
#
#   ./capture-env.sh
#
# Run from the repo root (the directory containing cobaltmine/ and cobaltcore/).
# Adjust BACKEND / FRONTEND below if your paths differ.
#
# WHY THIS DOES NOT JUST RUN `pip freeze`:
# your Python lives in an anaconda env (cr311), and install.txt shows a mix
# of `conda install` and `pip install`. A conda env's freeze output contains
# lines like
#     fastapi @ file:///croot/fastapi_1699887352/work
# which are paths on YOUR disk and install nowhere else. So this resolves
# requirements.in in a throwaway plain venv and freezes that instead.
set -euo pipefail

BACKEND=./cobaltmine/src/py
FRONTEND=./cobaltcore
PYTHON="${PYTHON:-python3.11}"

[ -d "$BACKEND" ]  || { echo "backend not found at $BACKEND — edit BACKEND"; exit 1; }
[ -d "$FRONTEND" ] || { echo "frontend not found at $FRONTEND — edit FRONTEND"; exit 1; }
[ -f "$BACKEND/requirements.in" ] || { echo "put requirements.in in $BACKEND first"; exit 1; }

echo "==> python: resolving requirements.in in a clean venv"
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
"$PYTHON" -m venv "$TMP/venv"
"$TMP/venv/bin/pip" install -q --upgrade pip
"$TMP/venv/bin/pip" install -q -r "$BACKEND/requirements.in"

"$TMP/venv/bin/pip" freeze --exclude-editable \
  | grep -v '@ file://' \
  | grep -viE '^(pip|setuptools|wheel)==' \
  > "$BACKEND/requirements.txt"
echo "    $BACKEND/requirements.txt — $(wc -l < "$BACKEND/requirements.txt" | tr -d ' ') packages pinned"

echo "==> python: pinning the interpreter"
"$PYTHON" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' \
  > "$BACKEND/.python-version"
echo "    python $(cat "$BACKEND/.python-version")"

echo "==> node: lockfile"
if [ -f "$FRONTEND/package-lock.json" ]; then
  echo "    package-lock.json present — that IS the pin, keep it committed"
else
  echo "    MISSING package-lock.json — run 'npm install' in $FRONTEND and commit it"
fi

echo "==> node: pinning the runtime"
node -v | sed 's/^v//' | cut -d. -f1 > "$FRONTEND/.nvmrc"
echo "    node $(cat "$FRONTEND/.nvmrc")"

echo "==> config templates (shape only — never the real secret)"
cat > "$BACKEND/.env.example" <<'ENV'
# Copy to .env in the directory you launch uvicorn from, then fill in.
# Generate the key:  python -c "import secrets; print(secrets.token_urlsafe(48))"
SECRET_KEY=
CORS_ORIGINS=http://localhost:3000
# Absolute path. A relative path follows your shell's working directory and
# will silently create a second, empty database.
DATABASE_URL=sqlite:////ABSOLUTE/PATH/TO/cobaltmine/src/py/users.db
ENV
cat > "$FRONTEND/.env.example" <<'ENV'
# Copy to .env in the frontend root.
# No secrets here — REACT_APP_* is compiled into the public bundle.
REACT_APP_API_URL=http://localhost:8000/api
ENV
echo "    $BACKEND/.env.example"
echo "    $FRONTEND/.env.example"

echo "==> gitignore"
for target in "$BACKEND/.gitignore" "$FRONTEND/.gitignore"; do
  touch "$target"
  grep -qxF '.env' "$target" || { echo '.env' >> "$target"; echo "    added .env to $target"; }
done

echo
echo "commit:"
echo "  $BACKEND/requirements.in"
echo "  $BACKEND/requirements.txt"
echo "  $BACKEND/.python-version"
echo "  $BACKEND/.env.example"
echo "  $FRONTEND/package-lock.json"
echo "  $FRONTEND/.nvmrc"
echo "  $FRONTEND/.env.example"
echo
echo "do NOT commit: .env (either one), users.db, data/model_data/"