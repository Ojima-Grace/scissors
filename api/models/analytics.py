from ..utils import db
from datetime import datetime

class Analytic(db.Model):
    __tablename__ = 'analytic'
    id = db.Column(db.Integer, primary_key=True)
    short_url_id = db.Column(db.Integer(), db.ForeignKey('shorturls.id'), nullable=False)
    click_timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(256))

    def __repr__(self):
        return f"<Shorturl {self.id}>"
    
    def save(self):
        db.session.add(self)
        db.session.commit()
    
    def update(self):
        db.session.commit()
    
    def delete(self):
        db.session.delete(self)
        db.session.commit()
    