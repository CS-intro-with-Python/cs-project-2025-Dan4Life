#!/usr/bin/env bash
set -e
export FLASK_APP="app.app:create_app" 
exec "$@"