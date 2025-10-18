#!/usr/bin/env bash
# start.sh - fallback start script for Render
exec gunicorn -k eventlet -w 1 app:app
