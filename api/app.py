import os, shlex, secrets, subprocess
from datetime import datetime
from flask import Flask, jsonify, request
from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import Session
from passlib.hash import bcrypt

from config import settings
from models import Base, User, Principal, Host, UserPrincipal, HostPrincipal, CertIssue

def create_app():
    app = Flask(__name__)

    engine = create_engine(settings.DB_URL, future=True)
    Base.metadata.create_all(engine)

    def next_serial(s: Session) -> int:
        cur = s.scalar(select(func.max(CertIssue.serial)))
        return (cur or 0) + 1

    # -------- Health ----------
    @app.get("/api/v1/health")
    def health():
        return jsonify(ok=True, time=datetime.utcnow().isoformat())

    # -------- Users CRUD ----------
    @app.get("/api/v1/users")
    def users_list():
        with Session(engine) as s:
            rows = s.query(User).order_by(User.username).all()
            return jsonify([{
                "id": u.id, "username": u.username, "email": u.email,
                "active": bool(u.active),
                "principals": [p.name for p in u.principals]
            } for u in rows])

    @app.post("/api/v1/users")
    def users_create():
        body = request.get_json(force=True, silent=True) or {}
        username = (body.get("username") or "").strip()
        if not username: return jsonify(error="username required"), 400
        with Session(engine) as s:
            if s.query(User).filter_by(username=username).first():
                return jsonify(error="exists"), 409
            pwd = body.get("password") or secrets.token_hex(12)
            u = User(
                username=username,
                email=body.get("email"),
                active=bool(body.get("active", True)),
                password_hash=bcrypt.hash(pwd)
            )
            s.add(u); s.commit()
            return jsonify(id=u.id), 201

    @app.patch("/api/v1/users/<int:uid>")
    def users_update(uid: int):
        body = request.get_json(force=True, silent=True) or {}
        with Session(engine) as s:
            u = s.get(User, uid)
            if not u: return jsonify(error="not found"), 404
            if "username" in body: u.username = body["username"]
            if "email" in body: u.email = body["email"]
            if "active" in body: u.active = bool(body["active"])
            if body.get("password"): u.password_hash = bcrypt.hash(body["password"])
            s.commit()
            return jsonify(ok=True)

    @app.delete("/api/v1/users/<int:uid>")
    def users_delete(uid: int):
        with Session(engine) as s:
            u = s.get(User, uid)
            if not u: return jsonify(error="not found"), 404
            s.delete(u); s.commit()
            return jsonify(ok=True)

    @app.put("/api/v1/users/<int:uid>/principals")
    def users_set_principals(uid: int):
        body = request.get_json(force=True, silent=True) or {}
        principal_ids = [int(x) for x in body.get("principal_ids", [])]
        with Session(engine) as s:
            if not s.get(User, uid): return jsonify(error="user not found"), 404
            s.query(UserPrincipal).filter_by(user_id=uid).delete()
            for pid in principal_ids:
                s.add(UserPrincipal(user_id=uid, principal_id=pid))
            s.commit()
            return jsonify(ok=True)

    # -------- Principals ----------
    @app.get("/api/v1/principals")
    def principals_list():
        with Session(engine) as s:
            items = s.query(Principal).order_by(Principal.name).all()
            return jsonify([{"id": p.id, "name": p.name} for p in items])

    @app.post("/api/v1/principals")
    def principals_create():
        body = request.get_json(force=True, silent=True) or {}
        name = (body.get("name") or "").strip()
        if not name: return jsonify(error="name required"), 400
        with Session(engine) as s:
            if s.query(Principal).filter_by(name=name).first():
                return jsonify(error="exists"), 409
            p = Principal(name=name); s.add(p); s.commit()
            return jsonify(id=p.id), 201

    @app.delete("/api/v1/principals/<int:pid>")
    def principals_delete(pid: int):
        with Session(engine) as s:
            p = s.get(Principal, pid)
            if not p: return jsonify(error="not found"), 404
            s.delete(p); s.commit()
            return jsonify(ok=True)

    # -------- Hosts ----------
    @app.get("/api/v1/hosts")
    def hosts_list():
        with Session(engine) as s:
            items = s.query(Host).order_by(Host.hostname).all()
            return jsonify([{
                "id": h.id, "hostname": h.hostname,
                "principals": [p.name for p in h.principals],
                "has_token": bool(h.api_token)
            } for h in items])

    @app.post("/api/v1/hosts")
    def hosts_create():
        body = request.get_json(force=True, silent=True) or {}
        hostname = (body.get("hostname") or "").strip()
        if not hostname: return jsonify(error="hostname required"), 400
        with Session(engine) as s:
            if s.query(Host).filter_by(hostname=hostname).first():
                return jsonify(error="exists"), 409
            token = secrets.token_hex(24)
            h = Host(hostname=hostname, api_token=token)
            s.add(h); s.commit()
            return jsonify(id=h.id, api_token=token), 201

    @app.patch("/api/v1/hosts/<int:hid>")
    def hosts_update(hid: int):
        body = request.get_json(force=True, silent=True) or {}
        with Session(engine) as s:
            h = s.get(Host, hid)
            if not h: return jsonify(error="not found"), 404
            if "hostname" in body: h.hostname = body["hostname"]
            s.commit()
            return jsonify(ok=True)

    @app.post("/api/v1/hosts/<int:hid>/rotate-token")
    def hosts_rotate_token(hid: int):
        with Session(engine) as s:
            h = s.get(Host, hid)
            if not h: return jsonify(error="not found"), 404
            h.api_token = secrets.token_hex(24); s.commit()
            return jsonify(api_token=h.api_token)

    @app.put("/api/v1/hosts/<int:hid>/principals")
    def hosts_set_principals(hid: int):
        body = request.get_json(force=True, silent=True) or {}
        principal_ids = [int(x) for x in body.get("principal_ids", [])]
        with Session(engine) as s:
            if not s.get(Host, hid): return jsonify(error="host not found"), 404
            s.query(HostPrincipal).filter_by(host_id=hid).delete()
            for pid in principal_ids:
                s.add(HostPrincipal(host_id=hid, principal_id=pid))
            s.commit()
            return jsonify(ok=True)

    # -------- Signing (User flow) ----------
    @app.get("/api/v1/user-principals")
    def user_principals():
        username = (request.args.get("username") or "").strip()
        if not username:
            return jsonify(error="username required"), 400
        with Session(engine) as s:
            u = s.query(User).filter_by(username=username).first()
            if not u:
                return jsonify(principals=[])
            return jsonify(principals=[p.name for p in u.principals])

    @app.get("/api/v1/ca.pub")
    def ca_pub():
        try:
            with open(settings.CA_PUB, "r", encoding="utf-8") as f:
                return jsonify(public_key=f.read().strip())
        except FileNotFoundError:
            return jsonify(error="CA public key not found"), 404

    @app.post("/api/v1/sign")
    def sign():
        """
        payload: { username, public_key, principals: [], ttl?, key_id? }
        """
        body = request.get_json(force=True, silent=True) or {}
        username = (body.get("username") or "").strip()
        principals = body.get("principals") or []
        ttl = (body.get("ttl") or settings.DEFAULT_TTL).strip()
        key_id = (body.get("key_id") or f"{username}-{int(datetime.utcnow().timestamp())}").strip()
        pub_key = (body.get("public_key") or "").strip()

        if not username or not pub_key or not principals:
            return jsonify(error="username, public_key, principals required"), 400

        # Persist temp public key to file
        pub_path = f"/tmp/{secrets.token_hex(8)}.pub"
        with open(pub_path, "w", encoding="utf-8") as f:
            f.write(pub_key)

        # Assemble ssh-keygen command
        principal_csv = ",".join(principals)
        with Session(engine) as s:
            serial = next_serial(s)
            cmd = [
                "ssh-keygen", "-s", settings.CA_PRIV,
                "-I", key_id,
                "-n", principal_csv,
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
                subprocess.run(cmd, check=True, capture_output=True, text=True)
                cert_path = pub_path + "-cert.pub"
                with open(cert_path, "r", encoding="utf-8") as f:
                    certificate = f.read().strip()

                s.add(CertIssue(
                    username=username,
                    principals=principal_csv,
                    key_id=key_id,
                    serial=serial,
                    ttl=ttl
                ))
                s.commit()
                return jsonify(key_id=key_id, serial=serial, certificate=certificate)
            except subprocess.CalledProcessError as e:
                return jsonify(error="signing failed", stderr=e.stderr), 500

    @app.get("/api/v1/cert-issues")
    def cert_issues():
        with Session(engine) as s:
            rows = s.query(CertIssue).order_by(CertIssue.id.desc()).limit(50).all()
            return jsonify([{
                "id": c.id, "username": c.username, "principals": c.principals.split(","),
                "key_id": c.key_id, "serial": c.serial, "ttl": c.ttl,
                "created_at": c.created_at.isoformat()
            } for c in rows])

    return app
