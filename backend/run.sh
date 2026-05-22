#!/usr/bin/env sh
echo "Starting Granian ASGI server..."

# Принудительно удаляем зависший сокет от предыдущего запуска
rm -f /tmp/sockets/granian.sock

exec granian \
    --uds /tmp/sockets/granian.sock \
    --uds-permissions 0666 \
    --interface asgi \
    src.main:app
