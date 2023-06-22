from ..utils import db
from datetime import datetime

class Shorturl(db.Model):
     __tablename__='shorturls'
     id = db.Column(db.Integer(), primary_key=True)
     long_url = db.Column(db.String(700), nullable=False)
     short_url = db.Column(db.String(20), nullable=False, unique=True)
     user_id = db.Column(db.Integer(), db.ForeignKey('users.id'))
     date_created = db.Column(db.DateTime(), default=datetime.utcnow, nullable=False)
     click_count = db.Column(db.Integer(), default=0)
     analytics = db.relationship('Analytic', backref='shorturl', lazy=True)
     #qrcodes = db.relationship('Qrcode', backref='shorturl_parent', lazy=True)
     #generated_qrcodes = db.relationship('Qrcode', backref='shorturl', lazy=True)
     generated_qrcodes = db.relationship('Qrcode', backref='shorturl_entry', lazy=True)
     user = db.relationship('User', back_populates='shorturl_entries', overlaps="shorturl_entries")

     def __repr__(self):
        return f"<Shorturl {self.id}>"
    
     def __init__(self, short_url, long_url, user=None, click_count=0):
        self.short_url = short_url
        self.long_url = long_url
        self.user_id = user
        self.click_count = click_count

     def save(self):
        db.session.add(self)
        db.session.commit()
    
     def delete(self):
        db.session.delete(self)
        db.session.commit()