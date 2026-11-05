#!/bin/bash
# One-time setup to make the LOCAL app look like a real site for recording.
# Everything here is local and reversible (see teardown.sh). Review before running.
set -e
ALIAS_IP=127.0.0.77
DOMAIN=hacking.beamreach.ai

echo "1) loopback alias so VaultBank owns :80 without touching your nginx"
sudo ifconfig lo0 alias $ALIAS_IP up

echo "2) /etc/hosts entry so $DOMAIN resolves locally"
if ! grep -q "$DOMAIN" /etc/hosts; then
  echo "$ALIAS_IP  $DOMAIN" | sudo tee -a /etc/hosts >/dev/null
fi

echo "3) start the target on the alias IP"
docker compose -f docker-compose.record.yml up -d --build

echo "done -> http://$DOMAIN  (admin panel: http://$DOMAIN:8080)"
