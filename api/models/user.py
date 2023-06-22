from ..utils import db
from datetime import datetime


class User(db.Model):
    __tablename__='users'
    id = db.Column(db.Integer(), primary_key=True)
    firstname = db.Column(db.String(30), nullable=False)
    lastname = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(50), nullable=False, unique=True)
    password_hash = db.Column(db.Text(), nullable=True)
    date_created = db.Column(db.DateTime(), default=datetime.utcnow, nullable=False)
    shorturl_entries = db.relationship('Shorturl', back_populates='user', overlaps="shorturl_entries")
    qrcodes = db.relationship('Qrcode', backref='qrcode', lazy=True)

    def __repr__(self):
        return f"<User {self.firstname}>"
    
    def save(self):
        db.session.add(self)
        db.session.commit()
    
    