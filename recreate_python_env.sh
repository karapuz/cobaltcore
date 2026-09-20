#!/usr/bin/env bash
# Recreate the Python environment on a fresh Ubuntu 24.04 Linode.
# Run as root:   bash recreate-python-env.sh
set -euo pipefail

APP_DIR=/srv/compass-app
DATA_DIR=/srv/compass-data
BACKEND="$APP_DIR/backend"

echo "==> system packages"
apt-get update -qq
# Ubuntu 24.04 ships Python 3.12. The app runs on it — no deadsnakes PPA,
# no pyenv. Only add those if something forces you back to 3.11.
apt-get install -y -qq python3 python3-venv python3-dev build-essential curl

echo "==> service user and directories"
id compass >/dev/null 2>&1 || adduser --system --group --home "$APP_DIR" compass
mkdir -p "$BACKEND" "$DATA_DIR/meta" /etc/compass
chown -R compass:compass "$APP_DIR" "$DATA_DIR"

echo "==> virtualenv"
sudo -u compass python3 -m venv "$APP_DIR/venv"
sudo -u compass "$APP_DIR/venv/bin/pip" install -q --upgrade pip

echo "==> python version"
"$APP_DIR/venv/bin/python" --version

cat <<'NOTE'

Next, from your laptop, copy the backend code over:

    rsync -az --exclude '__pycache__' --exclude '*.pyc' --exclude '.venv' \
          --exclude '.env' --exclude 'users.db' \
          cobaltmine/src/py/  compass@<IP>:/srv/compass-app/backend/

Then back on the server:

    sudo -u compass /srv/compass-app/venv/bin/pip install \
        -r /srv/compass-app/backend/requirements.txt

    sudo -u compass /srv/compass-app/venv/bin/python -c "import bcrypt; print(bcrypt.__version__)"
        # must print 4.x — 5.x breaks password hashing

Create /etc/compass/compass.env (chmod 600, owned by compass):

    SECRET_KEY=<python3 -c "import secrets; print(secrets.token_urlsafe(48))">
    CORS_ORIGINS=http://<IP>:8000
    DATABASE_URL=sqlite:////srv/compass-data/users.db
    COMPASS_DATA_DIR=/srv/compass-data

Generate the reference data and smoke test:

    cd /srv/compass-app/backend
    sudo -u compass env $(cat /etc/compass/compass.env | xargs) \
        /srv/compass-app/venv/bin/python build_entities.py

    sudo -u compass env $(cat /etc/compass/compass.env | xargs) \
        /srv/compass-app/venv/bin/uvicorn app.main:app --port 8000
    curl http://127.0.0.1:8000/api/health

NOTE