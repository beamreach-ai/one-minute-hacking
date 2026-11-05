#!/bin/bash
# Undo everything setup.sh did. Run this after the shoot.
ALIAS_IP=127.0.0.77
DOMAIN=hacking.beamreach.ai
docker compose -f docker-compose.record.yml down 2>/dev/null || true
sudo sed -i '' "/$DOMAIN/d" /etc/hosts
sudo ifconfig lo0 -alias $ALIAS_IP 2>/dev/null || true
echo "torn down: container stopped, hosts line removed, loopback alias released"
