from app import create_app, db
from app.models.user import User
from app.models.scheme import Scheme

def seed_database():
    """
    Seeds the database with a test user and schemes to verify the recommendation engine.
    """
    app = create_app()
    
    with app.app_context():
        print("🗑️  Dropping old tables...")
        db.drop_all()
        
        print("🏗️  Creating new tables...")
        db.create_all()

        # ==========================================
        # 1. CREATE TEST USER
        # ==========================================
        print("👤 Creating Test User (Rahul)...")
        
        user = User(
            email="rahul@example.com",
            password="hashed_password_123", # In real app, use generate_password_hash
            full_name="Rahul Kumar",
            age=30,
            income=50000.00,          # 50k Annual Income
            state="Uttar Pradesh",
            occupation="Farmer",
            category="General",
            documents=["Aadhar Card", "Land Proof"] # He has these docs
        )
        db.session.add(user)
        db.session.flush() # Flush to get the ID without committing yet
        print(f"   -> User created with ID: {user.id}")

        # ==========================================
        # 2. CREATE SCHEMES
        # ==========================================
        print("📜 Creating Schemes...")

        # SCHEME A: Perfect Match (Farmer + Low Income)
        scheme_1 = Scheme(
            name="PM Kisan Samman Nidhi",
            description="Income support of ₹6,000 per year for farmers.",
            link="https://pmkisan.gov.in",
            is_active=True,
            state="ALL",              # Available everywhere
            occupation="Farmer",      # Matches User
            category=None,            # Open to all categories
            min_age=18,
            max_age=None,
            min_income=0,
            max_income=100000,        # User fits
            required_documents=["Aadhar Card", "Land Proof"] # User has these
        )
        db.session.add(scheme_1)

        # SCHEME B: Mismatch (Occupation)
        # Should be REJECTED by Rule Engine because User is a Farmer, not Student
        scheme_2 = Scheme(
            name="National Scholarship Portal",
            description="Scholarships for students pursuing higher education.",
            link="https://scholarships.gov.in",
            is_active=True,
            state="Uttar Pradesh",
            occupation="Student",     # MISMATCH
            category="General",
            min_age=15,
            max_age=25,
            min_income=0,
            max_income=200000,
            required_documents=["Marksheet", "Aadhar Card"]
        )
        db.session.add(scheme_2)

        # SCHEME C: Mismatch (Income)
        # Should be REJECTED because User is too poor (Scheme is for rich people)
        scheme_3 = Scheme(
            name="High Tax Relief Scheme",
            description="Tax benefits for high income earners.",
            link="https://incometax.gov.in",
            is_active=True,
            state="ALL",
            occupation=None,
            category=None,
            min_age=25,
            max_age=60,
            min_income=500000,        # User earns 50k (Mismatch)
            max_income=10000000,
            required_documents=["PAN Card"]
        )
        db.session.add(scheme_3)

        # SCHEME D: Partial Match (State + Category, wrong occupation)
        # Should be ELIGIBLE (if occupation is nullable in scheme) but score lower than Scheme A
        scheme_4 = Scheme(
            name="UP General Welfare Scheme",
            description="General welfare for residents of UP.",
            link="http://up.gov.in",
            is_active=True,
            state="Uttar Pradesh",    # Matches
            occupation=None,          # Open to all
            category="General",       # Matches
            min_age=18,
            max_age=65,
            min_income=0,
            max_income=200000,
            required_documents=["Aadhar Card"] # User has this
        )
        db.session.add(scheme_4)

        # ==========================================
        # 3. COMMIT
        # ==========================================
        db.session.commit()
        print("\n✅ Database Seeded Successfully!")
        print(f"   -> User ID: {user.id}")
        print(f"   -> Test this endpoint: GET /api/recommendations/{user.id}")
        print("   -> Expected Result: Should return 'PM Kisan' and 'UP General Welfare'.")

if __name__ == "__main__":
    seed_database()