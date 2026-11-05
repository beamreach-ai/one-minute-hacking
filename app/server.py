#!/usr/bin/env python3
# ============================================================================
#  VaultBank — DELIBERATELY VULNERABLE demo app for the "1-Minute Hacking"
#  reel series. Every flaw here is intentional teaching material (OWASP top 10).
#  RUN LOCALLY ONLY. Never expose this to a real network.
# ============================================================================
import os, sqlite3, subprocess, time
from flask import (Flask, request, make_response, redirect, render_template,
                   send_file, jsonify, Response)
import jwt  # PyJWT

HERE = os.path.dirname(__file__)
DB = os.path.join(HERE, "vault.db")
DOCS = os.path.join(HERE, "docs")           # path-traversal base dir
WEBROOT = os.path.join(HERE, "webroot")     # holds the exposed .git + /.env
JWT_SECRET = "vault"                         # intentionally weak (crackable)

app = Flask(__name__, template_folder="templates", static_folder=None)


# ---- db helpers ------------------------------------------------------------
def db():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c


def init_db():
    c = db(); q = c.cursor()
    q.execute("CREATE TABLE IF NOT EXISTS users(username TEXT, pin TEXT, role TEXT, balance INTEGER)")
    q.execute("CREATE TABLE IF NOT EXISTS invoices(id INTEGER PRIMARY KEY, owner TEXT, customer TEXT, amount INTEGER, memo TEXT)")
    q.execute("DELETE FROM users"); q.execute("DELETE FROM invoices")
    users = [("admin", "1342", "admin", 284500),
             ("j.okafor", "7788", "user", 10420),
             ("m.lindqvist", "0420", "user", 980),
             ("s.petrova", "9931", "user", 54300)]
    q.executemany("INSERT INTO users VALUES(?,?,?,?)", users)
    names = ["Northwind Traders", "Acme Robotics", "Blue Harbor LLC", "Cedar & Co",
             "Meridian Health", "Orbital Freight", "Pinewood Studios", "Quill Media",
             "Riverside Dental", "Summit Outdoors", "Tallgrass Farms", "Umbra Design"]
    inv = [(1000 + i, "admin", n, 1200 + i * 337, f"Invoice #{1000+i}") for i, n in enumerate(names)]
    q.executemany("INSERT INTO invoices VALUES(?,?,?,?,?)", inv)
    c.commit(); c.close()


def make_token(username, role):
    return jwt.encode({"user": username, "role": role, "iat": int(time.time())},
                      JWT_SECRET, algorithm="HS256")


def read_token():
    t = request.cookies.get("session", "")
    try:
        return jwt.decode(t, JWT_SECRET, algorithms=["HS256"])
    except Exception:
        return None


# ---- 1 & 2: login (weak PIN brute-force + SQL injection) -------------------
@app.route("/")
def index():
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def login():
    u = request.form.get("username", "")
    p = request.form.get("pin", "")
    # VULN: string-built SQL -> SQLi ("admin' --"). Also weak 4-digit PIN -> brute force.
    sql = "SELECT username, role FROM users WHERE username = '%s' AND pin = '%s'" % (u, p)
    try:
        c = db(); row = c.execute(sql).fetchone(); c.close()
    except Exception:
        row = None
    if row:
        resp = make_response(redirect("/dashboard"))
        resp.set_cookie("session", make_token(row["username"], row["role"]))
        return resp
    # 200 (not 401) so form brute-forcers match on the failure string, not the status
    return render_template("login.html", error="Invalid credentials")


@app.route("/dashboard")
def dashboard():
    tok = read_token()
    if not tok:
        return redirect("/")
    c = db(); user = c.execute("SELECT * FROM users WHERE username=?", (tok["user"],)).fetchone(); c.close()
    bal = user["balance"] if user else 0
    return render_template("dashboard.html", user=tok["user"], role=tok["role"], balance=bal)


# ---- 7: forge admin JWT (weak secret) -> /admin ----------------------------
@app.route("/admin")
def admin():
    tok = read_token()
    if not tok or tok.get("role") != "admin":
        return Response("403 Forbidden — admin only", status=403)
    c = db(); users = c.execute("SELECT username, role, balance FROM users").fetchall(); c.close()
    return render_template("admin.html", users=users)


# ---- 3: path traversal / LFI ----------------------------------------------
@app.route("/download")
def download():
    f = request.args.get("file", "statement.txt")
    path = os.path.join(DOCS, f)           # VULN: no sanitization -> ../../etc/passwd
    try:
        with open(path) as fh:
            return Response(fh.read(), mimetype="text/plain")
    except Exception as e:
        return Response("error: %s" % e, status=404, mimetype="text/plain")


# ---- 4: OS command injection ----------------------------------------------
@app.route("/tools/ping", methods=["GET", "POST"])
def ping():
    host = request.values.get("host", "")
    if not host:
        return render_template("ping.html")
    # VULN: shell string concatenation -> `; id; cat /etc/passwd`
    out = subprocess.getoutput("ping -c 1 %s" % host)
    return Response(out, mimetype="text/plain")


# ---- 5: IDOR (no authorization on object id) -------------------------------
@app.route("/api/invoice/<int:iid>")
def invoice(iid):
    c = db(); row = c.execute("SELECT * FROM invoices WHERE id=?", (iid,)).fetchone(); c.close()
    if not row:
        return jsonify(error="not found"), 404
    return jsonify(dict(row))  # VULN: anyone can read any invoice id


# ---- 6 & 8: exposed .git and /.env (sensitive data) ------------------------
@app.route("/.env")
def dotenv():
    return send_file(os.path.join(WEBROOT, ".env"), mimetype="text/plain")


@app.route("/.git/<path:sub>")
def gitdir(sub):
    # VULN: the deployed .git directory is world-readable -> git-dumper
    p = os.path.join(WEBROOT, ".git", sub)
    if os.path.isfile(p):
        return send_file(p)
    return Response("404", status=404)


@app.route("/favicon.ico")
def favicon():
    return Response(status=204)


if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", "80"))
    app.run(host="0.0.0.0", port=port, threaded=True)
