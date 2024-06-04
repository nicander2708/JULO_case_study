from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import UUID

db = SQLAlchemy()

class WalletUser(db.Model):
    __tablename__ = "wallet_user"
    __table_args__ = {"schema": "public"}

    customer_xid = db.Column(UUID, index=True, primary_key=True)
    token = db.Column(db.VARCHAR(length=128), index=True, unique=True)

    def __repr__(self):
        return f'<Wllaet {self.customer_xid}>'
