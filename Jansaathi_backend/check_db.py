import sqlite3
import os

# Point directly to the ROOT folder Jansaathi_backend
# This bypasses the 'instance' folder which you confirmed is missing
db_path = os.path.join(os.getcwd(), 'users.db')

def verify_data():
    if not os.path.exists(db_path):
        print(f"❌ Database STILL not found at {db_path}")
        print("💡 Tip: Ensure you are running this script from C:\\Users\\devad\\Desktop\\Devadathan\\program\\Flutter\\Jansaathi_backend")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        # Check if the table exists first
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user';")
        if not cursor.fetchone():
            print("❌ Table 'user' does not exist in this database file.")
            return

        # Fetch all relevant profile fields
        cursor.execute("SELECT full_name, email, dob, location, nationality, phone FROM user")
        users = cursor.fetchall()
        
        if not users:
            print("⚠️ Database found, but the 'user' table is EMPTY. You may need to sign up again.")
        else:
            print(f"✅ Found {len(users)} user(s) in root database:\n")
            for u in users:
                print(f"👤 Name: {u[0]}")
                print(f"📧 Email: {u[1]}")
                print(f"📅 DOB: {u[2] if u[2] else 'Not Set'}")
                print(f"📍 Location: {u[3] if u[3] else 'Not Set'}")
                print(f"🌍 Nationality: {u[4] if u[4] else 'Not Set'}")
                print(f"📞 Phone: {u[5] if u[5] else 'Not Set'}")
                print("-" * 30)
                
    except Exception as e:
        print(f"❌ Error reading database: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    verify_data()