from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from sqlalchemy import String, Integer, Boolean, DateTime, UniqueConstraint

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

class Principal(Base):
    __tablename__ = "principals"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, index=True)

class Host(Base):
    __tablename__ = "hosts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    hostname: Mapped[str] = mapped_column(String(255), unique=True, index=True)

class UserPrincipal(Base):
    __tablename__ = "user_principals"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer)
    principal_id: Mapped[int] = mapped_column(Integer)
    __table_args__ = (UniqueConstraint("user_id","principal_id", name="u_user_principal"),)

class HostPrincipal(Base):
    __tablename__ = "host_principals"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    host_id: Mapped[int] = mapped_column(Integer)
    principal_id: Mapped[int] = mapped_column(Integer)
    __table_args__ = (UniqueConstraint("host_id","principal_id", name="u_host_principal"),)

class CertIssue(Base):
    __tablename__ = "cert_issues"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key_id: Mapped[str] = mapped_column(String(255), index=True)
    serial: Mapped[int] = mapped_column(Integer, index=True)
    principals: Mapped[str] = mapped_column(String(1024))
    pubkey_fingerprint: Mapped[str] = mapped_column(String(255))
    not_after: Mapped[DateTime] = mapped_column(DateTime)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)
