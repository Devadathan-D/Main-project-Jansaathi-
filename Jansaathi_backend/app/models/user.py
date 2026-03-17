from app.extensions import db

class User(db.Model):
    __tablename__ = "users"

    # ------------------------------
    # 1. IDENTIFICATION & AUTH
    # ------------------------------
    id = db.Column(db.Integer, primary_key=True)
    
    # Firebase UID (linked to Firebase Auth)
    firebase_uid = db.Column(db.String(100), unique=True, nullable=True, index=True)
    
    # Standard Auth
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password = db.Column(db.String(200), nullable=False) # Stores the HASHED password

    # ------------------------------
    # 2. PERSONAL PROFILE
    # ------------------------------
    full_name = db.Column(db.String(100), nullable=False)
    dob = db.Column(db.String(20))       # Stored as "DD-MM-YYYY" from Flutter
    gender = db.Column(db.String(20), nullable=True)  # <--- ADDED: Gender
    phone = db.Column(db.String(20))
    profile_image = db.Column(db.String(255))
    
    # Additional Personal Details
    location = db.Column(db.String(100), nullable=True)      # User's city/address
    nationality = db.Column(db.String(50), nullable=True)    # Nationality
    qualification = db.Column(db.String(50), nullable=True)  # Education level
    marital_status = db.Column(db.String(20), nullable=True) # Marital status

    # ------------------------------
    # 3. RECOMMENDATION DEMOGRAPHICS
    # ------------------------------
    # These fields power the logic for your app.
    
    age = db.Column(db.Integer, nullable=True)
    
    # INCOME: Stored as a Float.
    # Note: Your Flutter Provider converts the String (e.g., "$50k") 
    # to a Double (e.g., 75000.0) before sending it here.
    income = db.Column(db.Float, nullable=True)
    
    state = db.Column(db.String(100), nullable=True, index=True) # Used for location-based filtering
    occupation = db.Column(db.String(100), nullable=True, index=True)
    
    # CATEGORY: Stored as a String (e.g., "General", "OBC", "SC")
    category = db.Column(db.String(100), nullable=True, index=True) 

    # ------------------------------
    # 4. DOCUMENTS
    # ------------------------------
    # Stores a list of document filenames/URLs
    documents = db.Column(db.JSON, default=list)

    def __repr__(self):
        return f'<User {self.email}>'

    # ------------------------------
    # HELPER METHOD FOR API
    # ------------------------------
    def to_dict(self):
        """
        Converts the User object to a dictionary so it can be 
        sent as JSON in the API response.
        """
        return {
            "id": self.id,
            "firebase_uid": self.firebase_uid,
            "email": self.email,
            "full_name": self.full_name,
            "dob": self.dob,
            "gender": self.gender,       # <--- ADDED: Gender in response
            "phone": self.phone,
            "profile_image": self.profile_image,
            "location": self.location,
            "nationality": self.nationality,
            "qualification": self.qualification,
            "marital_status": self.marital_status,
            "age": self.age,
            "income": self.income,
            "state": self.state,
            "occupation": self.occupation,
            "category": self.category,
            "documents": self.documents if self.documents else []
        }