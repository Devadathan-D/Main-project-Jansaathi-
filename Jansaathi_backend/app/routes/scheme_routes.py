from flask import Blueprint, jsonify, request
from app.models.scheme import Scheme
from app.extensions import db
from sqlalchemy import or_
from scheme_utils import get_scheme_by_title, load_schemes_data

scheme_bp = Blueprint("schemes", __name__)


def _build_full_scheme_payload(scheme):
    """
    Merge SQL scheme data with rich JSON content from schemes.json.
    Ensures Flutter detail page always receives a 'content' block.
    """
    payload = scheme.to_dict()
    json_scheme = get_scheme_by_title(scheme.name)
    if not json_scheme and scheme.link:
        for block in load_schemes_data():
            for item in block.get("schemes", []):
                if item.get("scheme_url") == scheme.link:
                    json_scheme = {
                        "title": item.get("title"),
                        "category": block.get("category"),
                        "scheme_url": item.get("scheme_url"),
                        "content": item.get("content", {}),
                    }
                    break
            if json_scheme:
                break

    if json_scheme and isinstance(json_scheme.get("content"), dict):
        payload["content"] = json_scheme.get("content", {})
        payload["category"] = json_scheme.get("category") or payload.get("eligibility", {}).get("category")
        payload["scheme_url"] = json_scheme.get("scheme_url") or payload.get("scheme_url")
    else:
        description = (scheme.description or "").strip()
        payload["content"] = {"Details": [description]} if description else {}
        payload["category"] = payload.get("eligibility", {}).get("category")

    return payload

@scheme_bp.route("/", methods=["GET"])
def get_schemes():
    schemes = Scheme.query.filter_by(is_active=True).all()
    return jsonify({
        "status": "success",
        "count": len(schemes),
        "data": [s.to_dict() for s in schemes]
    })

# =========================
#// FIXED: SPLIT & SEARCH LOGIC
#// =========================
@scheme_bp.route('/category', methods=['GET', 'POST'])
def get_by_category():
    input_data = request.json.get('category') if request.is_json else request.args.get('category', '')
    
    # Normalize input to a list
    categories = []
    if isinstance(input_data, list):
        categories = input_data
    elif isinstance(input_data, str):
        categories = [input_data]
    
    if not categories:
        return jsonify([]), 200

    filters = []
    
    # IMPROVEMENT: Split categories by comma to handle "Agriculture, Rural..."
    # This allows "Agriculture" (DB) to match "Agriculture, Rural..." (Query)
    keywords = []
    for cat in categories:
        parts = cat.split(',')
        keywords.extend([p.strip() for p in parts])

    # Build filters for each keyword
    for word in keywords:
        search_term = f"%{word}%"
        filters.append(Scheme.category.ilike(search_term))
        filters.append(Scheme.name.ilike(search_term))
        filters.append(Scheme.description.ilike(search_term))

    query = Scheme.query.filter(Scheme.is_active == True, or_(*filters))
    schemes = query.all()
    
    # Debug print
    print(f"Keywords: {keywords} | Found: {len(schemes)} schemes")

    return jsonify([s.to_dict() for s in schemes]), 200

@scheme_bp.route('/carousel', methods=['GET'])
def carousel():
    schemes = Scheme.query.filter_by(is_active=True).order_by(Scheme.id.desc()).limit(5).all()
    return jsonify([s.to_dict() for s in schemes]), 200

@scheme_bp.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '')
    if not query:
        return jsonify([]), 200
        
    results = Scheme.query.filter(
        Scheme.is_active == True,
        (Scheme.name.ilike(f'%{query}%')) | 
        (Scheme.description.ilike(f'%{query}%'))
    ).all()
    
    return jsonify([s.to_dict() for s in results]), 200

# =========================
#// ADDED: DETAILS BY TITLE (FIXES 404 ERROR)
#// =========================
@scheme_bp.route('/details', methods=['POST'])
def get_scheme_details_by_title():
    """
    Fetches full scheme details based on Title.
    Flutter sends: { "title": "Scheme Name" }
    """
    data = request.get_json(silent=True)
    
    if not data or not data.get('title'):
        return jsonify({"status": "error", "message": "Title is required"}), 400
        
    search_title = data.get('title').strip()
    
    # Search for the scheme by name (prefer exact match, then partial)
    scheme = Scheme.query.filter(
        Scheme.is_active == True,
        Scheme.name.ilike(search_title)
    ).first()

    if not scheme:
        scheme = Scheme.query.filter(
            Scheme.is_active == True,
            Scheme.name.ilike(f"%{search_title}%")
        ).first()

    if not scheme:
        # Fallback for legacy rows where `name` is blank.
        for candidate in Scheme.query.filter(Scheme.is_active == True).all():
            generated = Scheme._format_title_from_link(candidate.link)
            if generated and generated.lower() == search_title.lower():
                scheme = candidate
                break
    
    if not scheme:
        return jsonify({
            "status": "error", 
            "message": "Scheme not found in database"
        }), 404

    return jsonify({
        "status": "success",
        "data": _build_full_scheme_payload(scheme)
    }), 200

# =========================
#// DETAILS BY ID
#// =========================
@scheme_bp.route('/<int:scheme_id>', methods=['GET'])
def get_scheme_detail(scheme_id):
    scheme = Scheme.query.get(scheme_id)
    
    if not scheme:
        return jsonify({
            "status": "error",
            "message": "Scheme not found"
        }), 404

    return jsonify({
        "status": "success",
        "data": _build_full_scheme_payload(scheme)
    }), 200
