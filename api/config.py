import os

class Settings:
    DB_URL = os.getenv("DB_URL", "sqlite:////data/sshca.db")
    CA_PRIV = os.getenv("CA_PRIV_KEY", "/data/ssh_ca")
    CA_PUB  = os.getenv("CA_PUB_KEY", "/data/ssh_ca.pub")
    DEFAULT_TTL = os.getenv("DEFAULT_CERT_TTL", "8h")

settings = Settings()
