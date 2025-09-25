from datetime import datetime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Boolean, Text, ForeignKey, DateTime, UniqueConstraint, Table

class Base(DeclarativeBase): pass

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    email: Mapped[str | None] = mapped_column(String(255))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    password_hash: Mapped[str | None] = mapped_column(String(255))

    principals: Mapped[list["Principal"]] = relationship(
        "Principal", secondary=lambda: UserPrincipal.__table__, back_populates="users"
    )

class Principal(Base):
    __tablename__ = "principals"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)

    users: Mapped[list[User]] = relationship(
        "User", secondary=lambda: UserPrincipal.__table__, back_populates="principals"
    )
    hosts: Mapped[list["Host"]] = relationship(
        "Host", secondary=lambda: HostPrincipal.__table__, back_populates="principals"
    )

class Host(Base):
    __tablename__ = "hosts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    hostname: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    api_token: Mapped[str | None] = mapped_column(String(255))

    principals: Mapped[list[Principal]] = relationship(
        "Principal", secondary=lambda: HostPrincipal.__table__, back_populates="hosts"
    )

class UserPrincipal(Base):
    __tablename__ = "user_principals"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    principal_id: Mapped[int] = mapped_column(ForeignKey("principals.id"), primary_key=True)

class HostPrincipal(Base):
    __tablename__ = "host_principals"
    host_id: Mapped[int] = mapped_column(ForeignKey("hosts.id"), primary_key=True)
    principal_id: Mapped[int] = mapped_column(ForeignKey("principals.id"), primary_key=True)

class CertIssue(Base):
    __tablename__ = "cert_issues"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(120))
    principals: Mapped[str] = mapped_column(Text)  # comma-separated
    key_id: Mapped[str] = mapped_column(String(255))
    serial: Mapped[int] = mapped_column(Integer)
    ttl: Mapped[str] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (UniqueConstraint("serial", name="uq_serial"),)
