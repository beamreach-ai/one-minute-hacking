#!/bin/sh
set -e
# recreate the "accidentally deployed" .git from the shipped tarball
if [ -f /srv/webroot/git-exposed.tar ] && [ ! -d /srv/webroot/.git ]; then
  tar -C /srv/webroot -xf /srv/webroot/git-exposed.tar
fi
python adminpanel.py &          # :8080 internal ops (default creds)
PORT=80 python server.py        # :80 main bank app
