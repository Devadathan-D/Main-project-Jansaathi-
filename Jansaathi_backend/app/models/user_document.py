from app.extensions import db
import datetime

class UserDocument(db.Model):
    __tablename__ = "user_documents"

    id = db.Column(db.Integer, primary_key=True)
    
    # Link to User (Integer ID is better for DB integrity than UID string)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    doc_type = db.Column(db.String(50)) # e.g., 'Aadhar', 'PAN'
    file_path = db.Column(db.String(255))
    is_verified = db.Column(db.Boolean, default=False)
    upload_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    # Relationship to easily access user info
    user = db.relationship("User", backref=db.backref("documents_uploaded", lazy=True))