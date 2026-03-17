from app import create_app, db
from app.models.scheme import Scheme

def debug_content():
    app = create_app()
    with app.app_context():
        # Fetch the first scheme in your database
        scheme = Scheme.query.first()
        
        if not scheme:
            print("❌ Database is empty. Run import_schemes_to_db.py first.")
            return

        print("="*50)
        print(f"Scheme Name: {scheme.name}")
        print("="*50)
        
        # Check the details column
        print(f"📦 Type of 'details' column: {type(scheme.details)}")
        
        if scheme.details is None:
            print("❌ CRITICAL ERROR: The 'details' column is NULL!")
            print("   -> This means you did not re-import the data after adding the column to the Model.")
            print("   -> SOLUTION: 1. Delete 'instance' folder. 2. Run 'python import_schemes_to_db.py'")
        elif isinstance(scheme.details, dict):
            print("✅ Details found! Keys are:")
            for key in scheme.details.keys():
                print(f"   - {key}")
        else:
            print(f"⚠️ Details is a String: {scheme.details[:50]}...")
            print("   -> It should be a Dictionary/JSON.")

if __name__ == "__main__":
    debug_content()