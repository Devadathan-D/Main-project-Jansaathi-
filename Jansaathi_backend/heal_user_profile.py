from app import create_app, db
from app.models.user import User
from app.utils.helpers import calculate_age_from_dob # Import helper

def heal_user():
    app = create_app()
    with app.app_context():
        print("🔧 Healing User Profile...")
        
        user = User.query.order_by(User.id.desc()).first()
        
        if not user:
            print("❌ No users found.")
            return

        print(f"Found user: {user.email}")

        # 1. SET A VALID DOB
        # Let's say user is born on 1st Jan 2004 (Makes them 20/21 years old)
        valid_dob = "2004-01-01" 
        
        # 2. CALCULATE AGE
        calculated_age = calculate_age_from_dob(valid_dob)

        # 3. UPDATE DATABASE
        user.dob = valid_dob
        user.age = calculated_age
        user.income = 50000.00
        user.occupation = "Student"
        user.location = "Delhi"
        user.state = "Delhi"
        user.category = "General"

        db.session.commit()
        
        print(f"✅ Updated Profile:")
        print(f"   DOB: {user.dob}")
        print(f"   Calculated Age: {user.age}")
        print("🚀 Check the 'Suggest' tab now!")

if __name__ == "__main__":
    heal_user()