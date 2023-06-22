from ..utils import db
from datetime import datetime

class Qrcode(db.Model):
    __tablename__ = 'qrcodes'
    id = db.Column(db.Integer(), primary_key=True)
    short_url_id = db.Column(db.Integer(), db.ForeignKey('shorturls.id'), nullable=False)
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id'))
    image = db.Column(db.LargeBinary, nullable=False)
    date_created = db.Column(db.DateTime(), default=datetime.utcnow, nullable=False)
    qr_identifier = db.Column(db.String(36), nullable=False)

    def __repr__(self):
        return f"<Qrcode {self.id}>"
    
    def save(self):
        db.session.add(self)
        db.session.commit()
    
    def update(self):
        db.session.commit()
    
    def delete(self):
        db.session.delete(self)
        db.session.commit()