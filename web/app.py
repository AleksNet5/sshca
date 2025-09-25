import os, shlex, subprocess, hashlib, tempfile, time, re
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from models import Base, User, Principal, Host, UserPrincipal, HostPrincipal, CertIssue

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET","dev")

DB_URL = os.getenv("DB_URL", "sqlite+pysqlite:////data/sshca.db")
engine = create_engine(DB_URL, future=True)
Base.metadata.create_all(engine)

CA_PRIV = os.getenv("CA_PRIV_KEY", "/keys/ssh_user_ca")
CA_PUB  = os.getenv("CA_PUB_KEY",  "/keys/ssh_user_ca.pub")
DEFAULT_TTL = os.getenv("DEFAULT_CERT_TTL","12h")

# ---------- helpers ----------
def ttl_to_timedelta(ttl: str) -> timedelta:
    total = 0
    for value, unit in re.findall(r"(\d+)([smhd])", ttl):
        v = int(value)
        total += v * (1 if unit=="s" else 60 if unit=="m" else 3600 if unit=="h" else 86400)
    return timedelta(seconds=total)

def get_user_principals(session: Session, username: str):
    u = session.execute(select(User).where(User.username==username, User.is_active==True)).scalar_one_or_none()
    if not u:
        return None, []
    rows = session.execute(
        select(Principal.name)
        .join(UserPrincipal, UserPrincipal.principal_id==Principal.id)
        .where(UserPrincipal.user_id==u.id)
    ).scalars().all()
    return u, rows

def get_host_principals(session: Session, hostname: str):
    h = session.execute(select(Host).where(Host.hostname==hostname)).scalar_one_or_none()
    if not h:
        return None, []
    rows = session.execute(
        select(Principal.name)
        .join(HostPrincipal, HostPrincipal.principal_id==Principal.id)
        .where(HostPrincipal.host_id==h.id)
    ).scalars().all()
    return h, rows

# ---------- health ----------
@app.get("/health")
def health():
    return "ok"

# ---------- minimal CRUD for bootstrap ----------
@app.post("/api/v1/users")
def create_user():
    data = request.get_json(force=True)
    username = data.get("username","").strip()
    is_active = bool(data.get("is_active", True))
    if not username: return jsonify({"error":"username required"}), 400
    with Session(engine) as s:
        u = s.execute(select(User).where(User.username==username)).scalar_one_or_none()
        if u: return jsonify({"error":"exists"}), 409
        s.add(User(username=username, is_active=is_active)); s.commit()
    return jsonify({"ok":True})

@app.post("/api/v1/principals")
def create_principal():
    data = request.get_json(force=True)
    name = data.get("name","").strip()
    if not name: return jsonify({"error":"name required"}), 400
    with Session(engine) as s:
        p = s.execute(select(Principal).where(Principal.name==name)).scalar_one_or_none()
        if p: return jsonify({"error":"exists"}), 409
        s.add(Principal(name=name)); s.commit()
    return jsonify({"ok":True})

@app.post("/api/v1/hosts")
def create_host():
    data = request.get_json(force=True)
    hostname = data.get("hostname","").strip()
    if not hostname: return jsonify({"error":"hostname required"}), 400
    with Session(engine) as s:
        h = s.execute(select(Host).where(Host.hostname==hostname)).scalar_one_or_none()
        if h: return jsonify({"error":"exists"}), 409
        s.add(Host(hostname=hostname)); s.commit()
    return jsonify({"ok":True})

@app.post("/api/v1/users/assign")
def assign_user_principal():
    data = request.get_json(force=True)
    username = data.get("username","").strip()
    principal = data.get("principal","").strip()
    if not username or not principal: return jsonify({"error":"username & principal required"}), 400
    with Session(engine) as s:
        u = s.execute(select(User).where(User.username==username)).scalar_one_or_none()
        p = s.execute(select(Principal).where(Principal.name==principal)).scalar_one_or_none()
        if not u or not p: return jsonify({"error":"unknown user or principal"}), 404
        exists = s.execute(select(UserPrincipal).where(
            UserPrincipal.user_id==u.id, UserPrincipal.principal_id==p.id
        )).scalar_one_or_none()
        if not exists:
            s.add(UserPrincipal(user_id=u.id, principal_id=p.id)); s.commit()
    return jsonify({"ok":True})

@app.post("/api/v1/hosts/assign")
def assign_host_principal():
    data = request.get_json(force=True)
    hostname = data.get("hostname","").strip()
    principal = data.get("principal","").strip()
    if not hostname or not principal: return jsonify({"error":"hostname & principal required"}), 400
    with Session(engine) as s:
        h = s.execute(select(Host).where(Host.hostname==hostname)).scalar_one_or_none()
        p = s.execute(select(Principal).where(Principal.name==principal)).scalar_one_or_none()
        if not h or not p: return jsonify({"error":"unknown host or principal"}), 404
        exists = s.execute(select(HostPrincipal).where(
            HostPrincipal.host_id==h.id, HostPrincipal.principal_id==p.id
        )).scalar_one_or_none()
        if not exists:
            s.add(HostPrincipal(host_id=h.id, principal_id=p.id)); s.commit()
    return jsonify({"ok":True})

# ---------- authorization for sshd ----------
@app.get("/api/v1/authorized-principals")
def authorized_principals():
    user = request.args.get("user","").strip()
    host = request.args.get("host","").strip()
    with Session(engine) as s:
        u, user_ps = get_user_principals(s, user)
        h, host_ps = get_host_principals(s, host)
    if not u or not h:
        # Return empty -> login denied
        return "", 200, {"Content-Type":"text/plain"}
    allowed = sorted(set(user_ps).intersection(host_ps))
    return ("\n".join(allowed) + ("\n" if allowed else "")), 200, {"Content-Type":"text/plain"}

# ---------- sign SSH user cert ----------
@app.post("/api/v1/sign")
def sign():
    data = request.get_json(force=True)
    username   = data.get("username","").strip()
    principals = data.get("principals",[])
    pubkey     = data.get("pubkey","").strip()
    ttl        = data.get("ttl", DEFAULT_TTL)

    if not username or not principals or not pubkey:
        return jsonify({"error":"username, principals[], pubkey required"}), 400

    with Session(engine) as s:
        u, user_ps = get_user_principals(s, username)
        if not u: return jsonify({"error":"unknown user"}), 404
    if not set(principals).issubset(set(user_ps)):
        return jsonify({"error":"requested principals not allowed for this user"}), 403

    with tempfile.NamedTemporaryFile("w", delete=False) as f:
        f.write(pubkey.strip() + "\n")
        pub_path = f.name

    key_id = f"{username}-{int(time.time())}"
    serial = int(time.time())

    cmd = [
        "ssh-keygen",
        "-s", CA_PRIV,
        "-I", key_id,
        "-n", ",".join(principals),
        "-V", f"+{ttl}",
        "-z", str(serial),
        "-O", "no-agent-forwarding",
        "-O", "no-pty",
        "-O", "no-user-rc",
        "-O", "no-x11-forwarding",
        "-O", "no-port-forwarding",
        pub_path
    ]

    try:
        subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)
        cert_path = pub_path + "-cert.pub"
        with open(cert_path,"r") as cf:
            cert_content = cf.read().strip()
        fp = hashlib.sha256(pubkey.encode()).hexdigest()[:32]
        not_after = datetime.utcnow() + ttl_to_timedelta(ttl)
        with Session(engine) as s:
            s.add(CertIssue(
                key_id=key_id, serial=serial,
                principals=",".join(principals),
                pubkey_fingerprint=fp,
                not_after=not_after
            ))
            s.commit()
        return jsonify({"key_id":key_id,"serial":serial,"cert":cert_content})
    except subprocess.CalledProcessError as e:
        return jsonify({"error":"sign failed","details":e.output}), 500
    finally:
        try:
            if os.path.exists(pub_path): os.unlink(pub_path)
            if os.path.exists(pub_path+"-cert.pub"): os.unlink(pub_path+"-cert.pub")
        except Exception:
            pass

# ---------- soft "revoke" via policy (deny auth) ----------
@app.post("/api/v1/revoke")
def revoke():
    data = request.get_json(force=True)
    serial = data.get("serial")
    if serial is None: return jsonify({"error":"serial required"}), 400
    with Session(engine) as s:
        row = s.execute(select(CertIssue).where(CertIssue.serial==int(serial))).scalar_one_or_none()
        if not row: return jsonify({"error":"unknown serial"}), 404
        row.revoked = True
        s.commit()
    # Note: with dynamic authorization, you can remove principal grants so that
    # AuthorizedPrincipalsCommand returns empty -> immediate deny.
    return jsonify({"status":"revoked","serial":serial})
