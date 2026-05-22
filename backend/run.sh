#!/usr/bin/env sh
echo "Starting Granian ASGI server..."
exec granian \
    --uds /tmp/sockets/granian.sock \
    --uds-permissions 0666 \
    --interface asgi \
    src.main:app