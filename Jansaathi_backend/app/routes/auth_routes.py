from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.user import User
from werkzeug.security import generate_password_hash, check_password_hash
from app.utils.helpers import calculate_age_from_dob
from sqlalchemy.exc import IntegrityError

# -------------------------------------------------------
# Blueprint Definition
# -------------------------------------------------------
auth_bp = Blueprint("auth", __name__)
# -------------------------------------------------------

# 🔹 HELPER: Convert Income String to Float
def convert_income_str_to_float(income_str):
    if not income_str:
        return 0.0
    try:
        s = income_str.lower()
        if "100,000+" in s: return 100000.0
        elif "50,000 - 100,000" in s: return 75000.0
        elif "20,000 - 50,000" in s: return 35000.0
        elif "less than" in s: return 20000.0
        else: return 0.0
    except Exception:
        return 0.0


def _verify_password(user: User, raw_password: str) -> bool:
    """
    Verify password for both current hashed records and legacy plain-text
    records that may exist from older endpoints.
    """
    if not user or not raw_password:
        return False

    stored = user.password or ""
    try:
        if check_password_hash(stored, raw_password):
            return True
    except Exception:
        # Not a Werkzeug hash format; fall back to legacy comparison below.
        pass

    # Legacy fallback (plain text)
    return stored == raw_password

@auth_bp.route('/signup', methods=['POST'])
def signup():
    data = request.get_json(silent=True)
    if not data:
        return jsonify(success=False, message="Invalid JSON"), 400

    required = ["email", "password"]
    if not all(data.get(k) for k in required):
        return jsonify(success=False, message="Missing required fields (email, password)"), 400

    try:
        # 1. Check if user exists
        if User.query.filter_by(email=data['email']).first():
            return jsonify(success=False, message="Email already registered"), 400

        # 2. Get DOB
        dob = data.get('dob', '')
        
        # 3. Calculate Age automatically
        calculated_age = calculate_age_from_dob(dob)

        # 4. PROCESS INCOME (Robust Handling)
        raw_income = data.get('income')
        
        # FIX: Check if Provider sent a Number, otherwise convert String
        if isinstance(raw_income, (int, float)):
            parsed_income = float(raw_income)
        else:
            parsed_income = convert_income_str_to_float(raw_income)

        # 5. Create User Object
        user = User(
            firebase_uid=data.get('firebase_uid'),
            full_name=data.get('full_name', 'Anonymous'),
            email=data['email'],
            password=generate_password_hash(data['password']),
            dob=dob,
            age=calculated_age, 
            location=data.get('location', ''), 
            nationality=data.get('nationality', ''),
            phone=data.get('phone', ''),
            gender=data.get('gender'),
            occupation=data.get('occupation', ''),
            qualification=data.get('qualification', ''),
            marital_status=data.get('marital_status', ''),
            
            # Recommendation Fields
            state=data.get('state', ''), 
            income=parsed_income, # <--- Parsed Float
            category=data.get('category')    
        )

        db.session.add(user)
        db.session.commit()

        return jsonify({
            "success": True, 
            "message": "User created", 
            "user_id": user.id
        }), 201

    except IntegrityError:
        db.session.rollback()
        return jsonify(success=False, message="Email already registered. Please login."), 400
    except Exception as e:
        db.session.rollback()
        print(f"❌ Signup Error: {e}")
        return jsonify(success=False, message=str(e)), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json(silent=True)
    if not data:
        return jsonify(success=False, message="Invalid JSON"), 400

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify(success=False, message="Email and password required"), 400

    user = User.query.filter_by(email=email).first()
    
    if not _verify_password(user, password):
        return jsonify(success=False, message="Invalid credentials"), 401

    return jsonify({
        "success": True, 
        "user": {
            "id": user.id,
            "firebase_uid": user.firebase_uid,
            "full_name": user.full_name,
            "email": user.email,
            "dob": user.dob,
            "location": user.location,
            "nationality": user.nationality,
            "phone": user.phone,
            "profile_image": user.profile_image,
            "occupation": user.occupation,
            "qualification": user.qualification,
            "marital_status": user.marital_status,
            "age": user.age,
            "income": user.income,
            "category": user.category,
            "state": user.state,
            "gender": user.gender,
            "documents": user.documents
        }
    }), 200


@auth_bp.route('/fallback-login', methods=['POST'])
def fallback_login():
    """
    Explicit endpoint for Flutter fallback when Firebase login fails
    due to network / reCAPTCHA / AppCheck issues.
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify(success=False, message="Invalid JSON"), 400

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify(success=False, message="Email and password required"), 400

    user = User.query.filter_by(email=email).first()
    if not _verify_password(user, password):
        return jsonify(success=False, message="Invalid credentials"), 401

    return jsonify({
        "success": True,
        "source": "backend_fallback",
        "user": {
            "id": user.id,
            "firebase_uid": user.firebase_uid,
            "full_name": user.full_name,
            "email": user.email,
            "dob": user.dob,
            "location": user.location,
            "nationality": user.nationality,
            "phone": user.phone,
            "profile_image": user.profile_image,
            "occupation": user.occupation,
            "qualification": user.qualification,
            "marital_status": user.marital_status,
            "age": user.age,
            "income": user.income,
            "category": user.category,
            "state": user.state,
            "gender": user.gender,
            "documents": user.documents
        }
    }), 200

@auth_bp.route('/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    data = request.get_json(silent=True)
    if not data:
        return jsonify(success=False, message="Invalid JSON"), 400

    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify(success=False, message="User not found"), 404

        # Update Basic Fields
        user.full_name = data.get('full_name', user.full_name)
        user.dob = data.get('dob', user.dob)
        user.location = data.get('location', user.location)
        user.occupation = data.get('occupation', user.occupation)
        user.qualification = data.get('qualification', user.qualification)
        user.nationality = data.get('nationality', user.nationality)
        user.phone = data.get('phone', user.phone)
        user.marital_status = data.get('marital_status', user.marital_status)
        user.gender = data.get('gender', user.gender)
        
        # Update Recommendation Fields
        user.state = data.get('state', data.get('location', user.location))
        
        # Handle Income Conversion (Robust Handling)
        raw_income = data.get('income')
        if raw_income is not None:
            # FIX: Check if Provider sent a Number, otherwise convert String
            if isinstance(raw_income, (int, float)):
                user.income = float(raw_income)
            else:
                user.income = convert_income_str_to_float(raw_income)
        
        user.category = data.get('category', user.category)

        # RECALCULATE AGE if DOB is changed
        if 'dob' in data:
            user.age = calculate_age_from_dob(user.dob)

        db.session.commit()

        return jsonify({
            "success": True, 
            "message": "Profile updated successfully"
        }), 200

    except Exception as e:
        db.session.rollback()
        print(f"❌ Update Error: {e}")
        return jsonify(success=False, message=str(e)), 500
