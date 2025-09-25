import os, tempfile, subprocess, hashlib, time, re
from datetime import datetime, timedelta
from fastapi import FastAPI, Depends, Query, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import select
from .db import SessionLocal, engine
from .models import Base, User, Principal, Host, UserPrincipal, HostPrincipal, CertIssue
from .schemas import SignRequest, SignResponse, RevokeRequest

Base.metadata.create_all(bind=engine)

app = FastAPI(title="SSH CA API")

app.add_middleware(
  CORSMiddleware,
  allow_origins=["*"],
  allow_methods=["*"],
  allow_headers=["*"],
)

CA_PRIV = os.getenv("CA_PRIV_KEY", "/keys/ssh_user_ca")
CA_PUB  = os.getenv("CA_PUB_KEY",  "/keys/ssh_user_ca.pub")
DEFAULT_TTL = os.getenv("DEFAULT_CERT_TTL","16h")

def get_db():
  db = SessionLocal()
  try:
    yield db
  finally:
    db.close()

@app.get("/health")
def health():
  return {"status":"ok"}

def parse_ttl(ttl: str) -> timedelta:
  total = 0
  for v,u in re.findall(r"(\d+)([smhd])", ttl):
    v = int(v)
    total += v * {"s":1,"m":60,"h":3600,"d":86400}[u]
  return timedelta(seconds=total or 0)

@app.get("/api/v1/authorized-principals", response_class=Response)
def authorized_principals(user: str = Query(""), host: str = Query(""), db: Session = Depends(get_db)):
  u = db.execute(select(User).where(User.username==user, User.is_active==True)).scalar_one_or_none()
  h = db.execute(select(Host).where(Host.hostname==host)).scalar_one_or_none()
  if not u or not h:
    return Response(content="", media_type="text/plain")
  user_p = db.execute(
    select(Principal.name)
    .join(UserPrincipal, UserPrincipal.principal_id==Principal.id)
    .where(UserPrincipal.user_id==u.id)
  ).scalars().all()
  host_p = db.execute(
    select(Principal.name)
    .join(HostPrincipal, HostPrincipal.principal_id==Principal.id)
    .where(HostPrincipal.host_id==h.id)
  ).scalars().all()
  allowed = sorted(set(user_p).intersection(host_p))
  return Response(content=("".join(p+"\n" for p in allowed)), media_type="text/plain")

@app.post("/api/v1/sign", response_model=SignResponse)
def sign(req: SignRequest, db: Session = Depends(get_db)):
  if not req.principals or not req.pubkey.strip():
    raise HTTPException(400, "principals[] and pubkey required")

  u = db.execute(select(User).where(User.username==req.username, User.is_active==True)).scalar_one_or_none()
  if not u: raise HTTPException(403, "unknown or inactive user")

  user_p = db.execute(
    select(Principal.name)
    .join(UserPrincipal, UserPrincipal.principal_id==Principal.id)
    .where(UserPrincipal.user_id==u.id)
  ).scalars().all()
  if not set(req.principals).issubset(set(user_p)):
    raise HTTPException(403, "requested principals not allowed for this user")

  with tempfile.NamedTemporaryFile("w", delete=False) as f:
    f.write(req.pubkey.strip() + "\n")
    pub_path = f.name

  key_id = f"{req.username}-{int(time.time())}"
  serial = int(time.time())

  cmd = [
    "ssh-keygen","-s",CA_PRIV,"-I",key_id,"-n",",".join(req.principals),
    "-V",f"+{req.ttl or DEFAULT_TTL}","-z",str(serial),
    "-O","no-agent-forwarding","-O","no-pty","-O","no-user-rc",
    "-O","no-x11-forwarding","-O","no-port-forwarding", pub_path
  ]
  try:
    subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)
    cert_path = pub_path + "-cert.pub"
    with open(cert_path,"r") as cf:
      cert = cf.read().strip()
    fp = hashlib.sha256(req.pubkey.encode()).hexdigest()[:32]
    not_after = datetime.utcnow() + parse_ttl(req.ttl or DEFAULT_TTL)
    db.add(CertIssue(
      key_id=key_id, serial=serial, principals=",".join(req.principals),
      pubkey_fingerprint=fp, not_after=not_after
    ))
    db.commit()
    return {"key_id":key_id,"serial":serial,"cert":cert}
  except subprocess.CalledProcessError as e:
    raise HTTPException(500, f"sign failed: {e.output}")
  finally:
    for p in (pub_path, pub_path+"-cert.pub"):
      try: os.unlink(p)
      except: pass

@app.post("/api/v1/revoke")
def revoke(req: RevokeRequest, db: Session = Depends(get_db)):
  row = db.execute(select(CertIssue).where(CertIssue.serial==req.serial)).scalar_one_or_none()
  if not row: raise HTTPException(404, "unknown serial")
  row.revoked = True
  db.commit()
  return {"status":"revoked","serial":req.serial}

@app.get("/api/v1/revoked_keys", response_class=Response)
def revoked_keys(db: Session = Depends(get_db)):
  serials = db.execute(select(CertIssue.serial).where(CertIssue.revoked==True)).scalars().all()
  lines = [f"@revoked serial:{s}" for s in sorted(serials)]
  return Response(content=("".join(l+"\n" for l in lines)), media_type="text/plain")
