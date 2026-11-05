# VaultBank Internal Ops — DEMO, default credentials (admin/admin) on purpose.
import os
from flask import Flask, request, render_template_string, redirect, make_response
app = Flask(__name__)
PAGE = """<!doctype html><title>VaultBank Ops</title>
<style>body{background:#0a0f1a;color:#e6eefb;font-family:system-ui;margin:0}
.b{max-width:420px;margin:60px auto;background:#121a2a;border:1px solid #223049;border-radius:14px;padding:26px}
input{width:100%;padding:11px;margin-top:6px;border-radius:8px;border:1px solid #223049;background:#0c1322;color:#e6eefb}
button{margin-top:16px;width:100%;padding:11px;border:0;border-radius:8px;background:#ff5c6c;color:#1a0309;font-weight:700}
h2{margin:0 0 4px}.m{color:#8fa0bd;font-size:.85rem}</style>
<div class="b"><h2>🔒 Internal Ops Console</h2><p class="m">Staff only · {{host}}</p>
{% if err %}<p style="color:#ff8ba0">{{err}}</p>{% endif %}
<form method=post><label class=m>Username</label><input name=u value="admin">
<label class=m>Password</label><input name=p type=password>
<button>Authenticate</button></form></div>"""
OPS = """<!doctype html><title>Ops</title><style>body{background:#0a0f1a;color:#e6eefb;font-family:system-ui;margin:0}
.b{max-width:620px;margin:50px auto;background:#121a2a;border:1px solid #223049;border-radius:14px;padding:26px}
.g{color:#39d98a}</style><div class="b"><h2 class="g">● ACCESS GRANTED — Internal Ops</h2>
<p>Welcome, administrator. Deploy pipeline, DB console and key vault are available here.</p>
<pre>prod-db-01    UP    vault-api   UP    key-vault   UNLOCKED</pre></div>"""
@app.route("/", methods=["GET","POST"])
def root():
    if request.method=="POST":
        if request.form.get("u")=="admin" and request.form.get("p")=="admin":
            return OPS
        return render_template_string(PAGE, err="Invalid credentials", host=request.host)
    return render_template_string(PAGE, err=None, host=request.host)
if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT","8080")))
