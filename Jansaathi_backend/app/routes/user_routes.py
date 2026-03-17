from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.user import User

# IMPORTANT: name must match import in __init__.py
user_bp = Blueprint("users", __name__)


# 🔹 Create User
@user_bp.route("/", methods=["POST"])
def create_user():
    data = request.get_json()

    if not data:
        return jsonify({"error": "No input data provided"}), 400

    # Basic validation
    if not data.get("email") or not data.get("full_name"):
        return jsonify({"error": "Email and Full Name are required"}), 400

    try:
        # Check if user already exists (since email is unique)
        if User.query.filter_by(email=data['email']).first():
            return jsonify({"error": "User with this email already exists"}), 400

        user = User(
            # Auth/Identity Fields (Required by Model)
            email=data.get("email"),
            full_name=data.get("full_name"),
            password=data.get("password"), # Optional if not using auth, but good to have
            firebase_uid=data.get("firebase_uid"),
            
            # Personal Info
            dob=data.get("dob"),
            location=data.get("location"),
            state=data.get("state"),
            nationality=data.get("nationality"),
            phone=data.get("phone"),
            
            # Profile Details
            occupation=data.get("occupation"),
            qualification=data.get("qualification"),
            marital_status=data.get("marital_status"),
            
            # Recommendation Fields
            age=data.get("age"),
            income=data.get("income"),
            category=data.get("category"),
            documents=data.get("documents", [])
        )

        db.session.add(user)
        db.session.commit()

        return jsonify({
            "status": "success",
            "message": "User created successfully",
            "data": {
                "id": user.id,
                "email": user.email
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        print(f"Error creating user: {e}")
        return jsonify({"error": str(e)}), 500


# 🔹 Get User By ID
@user_bp.route("/<int:user_id>", methods=["GET"])
def get_user(user_id):
    user = User.query.get(user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    # Return the full user object to match your Flutter Model expectations
    return jsonify({
        "status": "success",
        "data": {
            "id": user.id,
            "full_name": user.full_name,
            "email": user.email,
            "dob": user.dob,
            "age": user.age,
            "location": user.location,
            "state": user.state,
            "nationality": user.nationality,
            "phone": user.phone,
            "occupation": user.occupation,
            "qualification": user.qualification,
            "marital_status": user.marital_status,
            "income": user.income,
            "category": user.category,
            "profile_image": user.profile_image,
            "documents": user.documents
        }
    })


# 🔹 Update User
@user_bp.route("/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    user = User.query.get(user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json()

    if not data:
        return jsonify({"error": "No input data provided"}), 400

    try:
        # Update fields if they exist in the request
        # Personal Info
        user.full_name = data.get("full_name", user.full_name)
        user.dob = data.get("dob", user.dob)
        user.location = data.get("location", user.location)
        user.state = data.get("state", user.state)
        user.nationality = data.get("nationality", user.nationality)
        user.phone = data.get("phone", user.phone)
        
        # Profile
        user.occupation = data.get("occupation", user.occupation)
        user.qualification = data.get("qualification", user.qualification)
        user.marital_status = data.get("marital_status", user.marital_status)
        
        # Recommendation Fields
        user.age = data.get("age", user.age)
        user.income = data.get("income", user.income)
        user.category = data.get("category", user.category)
        
        # Documents (Replace whole list or append logic can go here)
        if "documents" in data:
            user.documents = data.get("documents")

        db.session.commit()

        return jsonify({
            "status": "success",
            "message": "User updated successfully",
            "data": {
                "id": user.id,
                "state": user.state,
                "income": user.income,
                "category": user.category
            }
        })
    except Exception as e:
        db.session.rollback()
        print(f"Error updating user: {e}")
        return jsonify({"error": str(e)}), 500


# 🔹 Delete User
@user_bp.route("/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    user = User.query.get(user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    try:
        db.session.delete(user)
        db.session.commit()
        return jsonify({
            "status": "success",
            "message": "User deleted successfully"
        })
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting user: {e}")
        return jsonify({"error": str(e)}), 500