#!/bin/sh
exec granian src.main:app \
    --host 0.0.0.0 \
    --port 8080 \
    --interface asgi
