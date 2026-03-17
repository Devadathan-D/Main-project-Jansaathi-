from flask import Blueprint, jsonify
from app.services.recommendation_service import (
    generate_document_smart_folders,
    generate_recommendations,
)

recommendation_bp = Blueprint("recommendation", __name__)

@recommendation_bp.route("/<int:user_id>", methods=["GET"])
def recommend(user_id):

    result = generate_recommendations(user_id)

    return jsonify({
        "status": "success" if not result["error"] else "error",
        "message": result["error"],
        "data": result["data"]
    })


@recommendation_bp.route("/<int:user_id>/smart-folders", methods=["GET"])
def smart_folders(user_id):
    result = generate_document_smart_folders(user_id)
    return jsonify({
        "status": "success" if not result["error"] else "error",
        "message": result["error"],
        "data": result["data"]
    })
