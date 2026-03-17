from collections import defaultdict
import os
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models.user import User
from app.models.user_document import UserDocument
from app.models.scheme import Scheme
from app.recommendation.rule_engine import is_eligible
from app.services.document_verification_service import (
    calculate_file_sha256,
    extract_text,
    normalize_doc_type,
    validate_document_payload,
    verify_document_text,
)


document_bp = Blueprint("documents", __name__)


def _find_user(user_id=None, uid=None):
    if user_id:
        try:
            return User.query.get(int(user_id))
        except (TypeError, ValueError):
            return None
    if uid:
        return User.query.filter_by(firebase_uid=uid).first()
    return None


def _normalize_doc_token(value):
    normalized = normalize_doc_type(value)
    if normalized:
        return normalized
    if value is None:
        return ""
    return str(value).strip().lower().replace(" ", "_")


def _document_to_response(document):
    doc_type = _normalize_doc_token(document.doc_type)
    status_text = "verified" if document.is_verified else "pending"

    return {
        "id": document.id,
        "title": doc_type.replace("_", " ").title(),
        "type": doc_type,
        "doc_type": doc_type,
        "verified": bool(document.is_verified),
        "verification_status": status_text,
        "status": status_text,
        "uploadedAt": document.upload_date.isoformat() if document.upload_date else None,
        "date": document.upload_date.strftime("%Y-%m-%d %H:%M:%S") if document.upload_date else None,
        "path": document.file_path,
        "fileUrl": document.file_path,
    }


def _sync_user_verified_documents(user):
    verified_docs = UserDocument.query.filter_by(user_id=user.id, is_verified=True).all()
    verified_types = sorted({
        _normalize_doc_token(doc.doc_type)
        for doc in verified_docs
        if _normalize_doc_token(doc.doc_type)
    })
    user.documents = verified_types


def _find_duplicate_document(user_id, normalized_doc_type, file_hash):
    existing_docs = UserDocument.query.filter_by(
        user_id=user_id,
        doc_type=normalized_doc_type,
    ).all()
    hash_prefix = f"{file_hash}_"

    for doc in existing_docs:
        basename = os.path.basename(doc.file_path or "")
        if basename.startswith(hash_prefix):
            return doc
    return None


@document_bp.route('/upload', methods=['POST'])
def upload_document():
    user_id = request.form.get('user_id')
    uid = request.form.get('uid')
    doc_type = request.form.get('doc_type')

    if 'file' not in request.files:
        return jsonify(success=False, message="Missing file"), 400

    file = request.files['file']

    is_valid, validation_message, normalized_doc_type = validate_document_payload(
        file_storage=file,
        doc_type=doc_type,
        config=current_app.config,
    )
    if not is_valid:
        return jsonify(success=False, message=validation_message), 400

    user = _find_user(user_id=user_id, uid=uid)

    if not user:
        return jsonify(success=False, message="User not found"), 404

    file_hash = calculate_file_sha256(file)
    duplicate_doc = _find_duplicate_document(user.id, normalized_doc_type, file_hash)
    if duplicate_doc:
        _sync_user_verified_documents(user)
        db.session.commit()
        return jsonify(
            success=True,
            duplicate=True,
            message="Duplicate document already uploaded",
            doc_id=duplicate_doc.id,
            verified=duplicate_doc.is_verified,
            doc_type=duplicate_doc.doc_type,
            validation_status="verified" if duplicate_doc.is_verified else "pending",
        ), 200

    user_dir = os.path.join(
        current_app.config['UPLOAD_FOLDER'],
        str(user.id),
        normalized_doc_type,
    )
    os.makedirs(user_dir, exist_ok=True)

    original_name = secure_filename(file.filename)
    filename = f"{file_hash}_{original_name}"
    path = os.path.join(user_dir, filename)
    file.save(path)

    verification = {
        "verified": False,
        "confidence": 0,
        "reasons": ["Verification failed"],
        "extracted_id": None,
    }
    try:
        text = extract_text(path)
        if text:
            verification = verify_document_text(text, normalized_doc_type)
        else:
            verification = {
                "verified": False,
                "confidence": 0,
                "reasons": ["No OCR text extracted (PDF/manual review required)"],
                "extracted_id": None,
            }
    except Exception as error:
        print(f"Document verification error: {error}")

    doc_record = UserDocument(
        user_id=user.id,
        doc_type=normalized_doc_type,
        file_path=path,
        is_verified=verification["verified"],
    )
    db.session.add(doc_record)

    _sync_user_verified_documents(user)
    db.session.commit()

    return jsonify(
        success=True,
        doc_id=doc_record.id,
        doc_type=normalized_doc_type,
        verified=verification["verified"],
        validation_status="verified" if verification["verified"] else "pending",
        confidence=verification["confidence"],
        reasons=verification["reasons"],
        extracted_id=verification["extracted_id"],
    ), 200


@document_bp.route('/list', methods=['POST'])
def list_documents():
    data = request.get_json(silent=True)
    if not data:
        return jsonify(success=False, message="Invalid JSON"), 400

    user = _find_user(user_id=data.get("user_id"), uid=data.get("uid"))

    if not user:
        return jsonify(success=False, message="User not found"), 404

    docs = (
        UserDocument.query.filter_by(user_id=user.id)
        .order_by(UserDocument.upload_date.desc())
        .all()
    )

    return jsonify([_document_to_response(doc) for doc in docs]), 200


@document_bp.route('/smart-folders', methods=['POST'])
def get_smart_folders():
    data = request.get_json(silent=True)
    if not data:
        return jsonify(success=False, message="Invalid JSON"), 400

    user = _find_user(user_id=data.get("user_id"), uid=data.get("uid"))
    if not user:
        return jsonify(success=False, message="User not found"), 404

    documents = UserDocument.query.filter_by(user_id=user.id).all()

    docs_by_type = defaultdict(list)
    verified_types = set()

    for doc in documents:
        doc_payload = _document_to_response(doc)
        token = doc_payload["doc_type"]
        docs_by_type[token].append(doc_payload)
        if doc_payload["verified"]:
            verified_types.add(token)

    schemes = Scheme.query.filter_by(is_active=True).all()
    eligible_schemes = [
        scheme
        for scheme in schemes
        if is_eligible(user, scheme, strict_documents=False, allow_missing_profile=True)
    ]

    folders = []
    for scheme in eligible_schemes:
        required_docs = scheme.required_documents or []
        if isinstance(required_docs, str):
            required_docs = [item.strip() for item in required_docs.split(',') if item.strip()]

        required_tokens = []
        for item in required_docs:
            token = _normalize_doc_token(item)
            if token and token not in required_tokens:
                required_tokens.append(token)

        matched_tokens = [token for token in required_tokens if token in verified_types]
        missing_tokens = [token for token in required_tokens if token not in verified_types]

        matched_documents = []
        for token in matched_tokens:
            matched_documents.extend(docs_by_type.get(token, []))

        completion = 100.0 if not required_tokens else round((len(matched_tokens) / len(required_tokens)) * 100.0, 2)

        folders.append({
            "scheme_id": scheme.id,
            "scheme_name": scheme.name,
            "required_documents": required_tokens,
            "matched_documents": matched_tokens,
            "missing_documents": missing_tokens,
            "completion_percent": completion,
            "uploaded_count": len(matched_tokens),
            "required_count": len(required_tokens),
            "documents": matched_documents,
        })

    folders.sort(key=lambda row: (-row["completion_percent"], row["scheme_name"].lower()))

    return jsonify(
        success=True,
        count=len(folders),
        data=folders,
    ), 200


@document_bp.route('/verify/<int:doc_id>', methods=['POST'])
def reverify_document(doc_id):
    doc = UserDocument.query.get(doc_id)
    if not doc:
        return jsonify(success=False, message="Document not found"), 404

    normalized_doc_type = normalize_doc_type(doc.doc_type)
    if not normalized_doc_type:
        return jsonify(success=False, message="Unsupported document type"), 400

    if not doc.file_path or not os.path.exists(doc.file_path):
        return jsonify(success=False, message="Stored document file not found"), 404

    verification = {
        "verified": False,
        "confidence": 0,
        "reasons": ["Verification failed"],
        "extracted_id": None,
    }

    try:
        text = extract_text(doc.file_path)
        if text:
            verification = verify_document_text(text, normalized_doc_type)
        else:
            verification = {
                "verified": False,
                "confidence": 0,
                "reasons": ["No OCR text extracted (PDF/manual review required)"],
                "extracted_id": None,
            }
    except Exception as error:
        print(f"Document re-verification error: {error}")

    doc.is_verified = verification["verified"]

    user = User.query.get(doc.user_id)
    if user:
        _sync_user_verified_documents(user)

    db.session.commit()

    return jsonify(
        success=True,
        doc_id=doc.id,
        doc_type=normalized_doc_type,
        verified=verification["verified"],
        validation_status="verified" if verification["verified"] else "pending",
        confidence=verification["confidence"],
        reasons=verification["reasons"],
        extracted_id=verification["extracted_id"],
    ), 200
