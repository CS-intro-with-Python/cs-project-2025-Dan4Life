#!/usr/bin/env bash
set -e
export FLASK_APP=app.py
flask db upgrade || true
exec "$@"