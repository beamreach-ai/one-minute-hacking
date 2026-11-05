# 1-Minute Hacking — VaultBank

A **deliberately vulnerable** demo app ("VaultBank") and the tooling behind the
*1-Minute Hacking* short-video series. Each reel exploits one textbook
[OWASP](https://owasp.org/Top10/) flaw against this app, in under a minute, with
a clean terminal payoff.

> ### ⚠️ Safety notice
> This app is **intentionally insecure**. It exists only to be attacked in a
> controlled, local demo. **Never deploy it to a public network or a machine you
> care about.** Run it on `localhost` (or a throwaway VM). Every "secret" in this
> repo is fake. Only ever point these tools at *this* app — attacking systems you
> don't own is illegal.

## Run it

```bash
docker compose up -d --build         # http://localhost:8899  (admin panel :8898)
```

For recording, `setup.sh` maps it to a believable local domain with a loopback
alias + `/etc/hosts` entry (no port, no clash with other local servers);
`teardown.sh` reverses everything.

## The nine flaws

| # | Class | Where | One-liner |
|---|-------|-------|-----------|
| 1 | Weak credentials | `POST /login` | `hydra -l admin -x 4:4:1 … http-post-form` |
| 2 | SQL injection | `POST /login` | username `admin' --` / `sqlmap` |
| 3 | Path traversal | `GET /download?file=` | `curl '…/download?file=../../../../etc/passwd'` |
| 4 | Command injection | `POST /tools/ping` | `host=x; id; cat /etc/passwd` |
| 5 | IDOR | `GET /api/invoice/<id>` | `for id in {1000..1012}; curl …` |
| 6 | Exposed `.git` | `/.git/` | `git-dumper http://…/.git ./loot` |
| 7 | Weak JWT secret | session cookie | `jwt_tool … -C -d wordlist` |
| 8 | Exposed `/.env` | `/.env` | `ffuf -w words -u http://…/FUZZ` |
| 9 | Default creds | `:8080` admin panel | `nmap` → `admin:admin` |

Exact capture commands: [`reels/attacks.md`](reels/attacks.md).

## Layout

```
app/              VaultBank Flask app (the target) + the 8080 ops panel
  webroot/        exposed /.env and the git-exposed.tar (unpacked at boot)
Dockerfile        builds the target image
docker-compose*.yml   dev (ports) and record (loopback alias) modes
setup.sh/teardown.sh  one-time recording setup and its clean undo
reels/player.py   the terminal-session reel renderer (slides + scroll + payoff)
```

Built by Beamreach for social content. Educational use only.
