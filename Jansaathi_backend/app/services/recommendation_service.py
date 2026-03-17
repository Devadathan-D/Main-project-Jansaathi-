from flask import current_app
from app.models.user import User
from app.models.user_document import UserDocument


DOC_ALIASES = {
    "aadhar": "aadhaar",
    "aadhaar card": "aadhaar",
    "aadhaar": "aadhaar",
    "pan card": "pan",
    "pan": "pan",
    "income certificate": "income_certificate",
    "caste certificate": "caste_certificate",
    "domicile certificate": "domicile_certificate",
    "residence proof": "residence_proof",
    "bank passbook": "bank_passbook",
    "bank statement": "bank_statement",
    "passport photo": "passport_photo",
    "passport": "passport",
    "voter id": "voter_id",
    "driving licence": "driving_license",
    "driving license": "driving_license",
    "ration card": "ration_card",
    "job card": "job_card",
    "land record": "land_record",
    "land records": "land_record",
}


SMART_FOLDER_RULES = {
    "IDENTITY VAULT": {
        "aadhaar",
        "pan",
        "passport",
        "voter_id",
        "driving_license",
        "passport_photo",
    },
    "FINANCIAL DOCS": {
        "income_certificate",
        "bank_passbook",
        "bank_statement",
        "salary_slip",
        "itr",
    },
}


def _normalize_document_name(value):
    raw = (str(value or "")).strip().lower()
    if not raw:
        return ""
    normalized = DOC_ALIASES.get(raw, raw)
    return normalized.replace(" ", "_")


def _to_document_list(value):
    if not value:
        return []
    if isinstance(value, list):
        return [v for v in value if str(v).strip()]
    if isinstance(value, str):
        return [v.strip() for v in value.split(",") if v.strip()]
    return [str(value)]


def _folder_for_document(document_name):
    for folder_name, doc_set in SMART_FOLDER_RULES.items():
        if document_name in doc_set:
            return folder_name
    return "GOVERNMENT SCHEMES"


def _collect_user_document_status(user):
    status = {}

    # Existing list field on User model (legacy source)
    for doc_name in _to_document_list(user.documents):
        normalized = _normalize_document_name(doc_name)
        if not normalized:
            continue
        status.setdefault(normalized, {"uploaded": False, "verified": False})
        status[normalized]["uploaded"] = True

    # Uploaded documents table (authoritative source)
    rows = UserDocument.query.filter_by(user_id=user.id).all()
    for row in rows:
        normalized = _normalize_document_name(row.doc_type)
        if not normalized:
            continue
        status.setdefault(normalized, {"uploaded": False, "verified": False})
        status[normalized]["uploaded"] = True
        if row.is_verified:
            status[normalized]["verified"] = True

    return status


def generate_document_smart_folders(user_id):
    user = User.query.get(user_id)
    if not user:
        return {
            "error": f"User with ID {user_id} not found",
            "data": {}
        }

    recommendation_result = generate_recommendations(user_id)
    if recommendation_result["error"]:
        return {
            "error": recommendation_result["error"],
            "data": {}
        }

    recommendations = recommendation_result["data"]
    user_status = _collect_user_document_status(user)

    scheme_document_analysis = []
    required_unique = set()

    for scheme in recommendations:
        required_docs = []
        required_raw = _to_document_list(scheme.get("required_documents"))
        seen = set()
        for doc_name in required_raw:
            normalized = _normalize_document_name(doc_name)
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            required_unique.add(normalized)

            doc_status = user_status.get(normalized, {"uploaded": False, "verified": False})
            required_docs.append({
                "name": normalized,
                "uploaded": doc_status["uploaded"],
                "verified": doc_status["verified"],
                "missing": not doc_status["uploaded"],
            })

        missing_docs = [d["name"] for d in required_docs if d["missing"]]
        scheme_document_analysis.append({
            "scheme_id": scheme.get("id"),
            "scheme_name": scheme.get("name"),
            "score": scheme.get("score"),
            "required_documents": required_docs,
            "missing_documents": missing_docs,
            "has_all_required_documents": len(missing_docs) == 0,
        })

    smart_folders = {
        "IDENTITY VAULT": [],
        "FINANCIAL DOCS": [],
        "GOVERNMENT SCHEMES": [],
    }

    for doc_name in sorted(required_unique):
        folder = _folder_for_document(doc_name)
        doc_status = user_status.get(doc_name, {"uploaded": False, "verified": False})
        smart_folders[folder].append({
            "name": doc_name,
            "uploaded": doc_status["uploaded"],
            "verified": doc_status["verified"],
            "missing": not doc_status["uploaded"],
        })

    folder_cards = []
    for folder_name in ("IDENTITY VAULT", "FINANCIAL DOCS", "GOVERNMENT SCHEMES"):
        docs = smart_folders[folder_name]
        total = len(docs)
        uploaded_count = sum(1 for d in docs if d["uploaded"])
        folder_cards.append({
            "folder": folder_name,
            "total_required": total,
            "uploaded_count": uploaded_count,
            "missing_count": total - uploaded_count,
            "is_empty": total == 0,
            "documents": docs,
        })

    total_required = len(required_unique)
    uploaded_total = sum(1 for doc_name in required_unique if user_status.get(doc_name, {}).get("uploaded"))
    missing_total = total_required - uploaded_total

    data = {
        "summary": {
            "total_required_documents": total_required,
            "uploaded_documents": uploaded_total,
            "missing_documents": missing_total,
            "coverage_percent": round((uploaded_total / total_required) * 100, 2) if total_required else 100.0,
        },
        "smart_folders": folder_cards,
        "scheme_document_analysis": scheme_document_analysis,
    }

    return {
        "error": None,
        "data": data
    }

def generate_recommendations(user_id):
    """
    Service layer function to handle the recommendation request.
    It acts as a bridge between the API Route and the Recommendation Engine.
    """
    
    # 1. VALIDATION: Does the user exist?
    user = User.query.get(user_id)
    if not user:
        return {
            "error": f"User with ID {user_id} not found",
            "data": []
        }

    # 2. ACCESS ENGINE: Get the pre-loaded engine from the app context
    # (We initialized 'app.recommender' inside app/__init__.py)
    try:
        recommender = current_app.recommender
    except AttributeError:
        return {
            "error": "Recommendation engine not initialized. Check app/__init__.py",
            "data": []
        }

    # 3. EXECUTE LOGIC: Run the recommendation algorithm
    try:
        # The heavy lifting (filtering, ranking, explaining) happens here
        all_recommendations = recommender.recommend(user_id)
        
        # 4. RETURN DATA: Format the response
        # We limit to top 5 as per your original requirement
        return {
            "error": None,
            "data": all_recommendations[:5] 
        }
        
    except Exception as e:
        # Catch any unexpected errors from the engine
        return {
            "error": f"Error generating recommendations: {str(e)}",
            "data": []
        }
