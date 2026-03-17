import hashlib
import os
import re
from typing import Dict, List, Optional, Tuple

from PIL import Image
import pytesseract

DEFAULT_TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
if os.path.exists(DEFAULT_TESSERACT_PATH):
    pytesseract.pytesseract.tesseract_cmd = DEFAULT_TESSERACT_PATH


SUPPORTED_DOC_TYPES = {
    "aadhaar": "aadhaar",
    "aadhar": "aadhaar",
    "pan": "pan",
}


DOC_RULES = {
    "aadhaar": {
        "keywords": ["government of india", "unique identification", "aadhaar"],
        "id_pattern": r"\b\d{4}\s?\d{4}\s?\d{4}\b",
    },
    "pan": {
        "keywords": ["income tax", "permanent account number", "govt. of india"],
        "id_pattern": r"\b[A-Z]{5}[0-9]{4}[A-Z]\b",
    },
}


def normalize_doc_type(doc_type: Optional[str]) -> Optional[str]:
    if not doc_type:
        return None
    normalized = SUPPORTED_DOC_TYPES.get(doc_type.strip().lower())
    return normalized


def is_allowed_extension(filename: str, allowed_extensions: set) -> bool:
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in allowed_extensions


def get_file_extension(filename: str) -> str:
    if "." not in filename:
        return ""
    return filename.rsplit(".", 1)[1].lower()


def calculate_file_sha256(file_storage) -> str:
    hasher = hashlib.sha256()
    file_storage.stream.seek(0)
    while True:
        chunk = file_storage.stream.read(8192)
        if not chunk:
            break
        hasher.update(chunk)
    file_storage.stream.seek(0)
    return hasher.hexdigest()


def validate_document_payload(file_storage, doc_type: Optional[str], config) -> Tuple[bool, str, Optional[str]]:
    normalized_doc_type = normalize_doc_type(doc_type)
    if not normalized_doc_type:
        return False, "Unsupported doc_type. Allowed: aadhaar, pan", None

    filename = (file_storage.filename or "").strip()
    if not filename:
        return False, "No file selected", None

    allowed_extensions = config.get("ALLOWED_EXTENSIONS", set())
    if not is_allowed_extension(filename, allowed_extensions):
        return False, "Unsupported file extension", None

    max_size = int(config.get("MAX_CONTENT_LENGTH", 16 * 1024 * 1024))
    file_storage.stream.seek(0, os.SEEK_END)
    size = file_storage.stream.tell()
    file_storage.stream.seek(0)
    if size <= 0:
        return False, "Uploaded file is empty", None
    if size > max_size:
        return False, "File exceeds maximum allowed size", None

    return True, "", normalized_doc_type


def extract_text(filepath: str) -> str:
    ext = get_file_extension(filepath)
    if ext == "pdf":
        return ""
    text = pytesseract.image_to_string(Image.open(filepath))
    return text or ""


def verify_document_text(raw_text: str, doc_type: str) -> Dict:
    text = (raw_text or "").lower()
    rule = DOC_RULES.get(doc_type)
    if not rule:
        return {
            "verified": False,
            "confidence": 0,
            "reasons": ["Unsupported document type for OCR verification"],
            "extracted_id": None,
        }

    reasons: List[str] = []
    keyword_hits = sum(1 for keyword in rule["keywords"] if keyword in text)
    keyword_score = min(40, keyword_hits * 15)
    if keyword_hits:
        reasons.append(f"Detected {keyword_hits} expected keyword(s)")
    else:
        reasons.append("No expected document keywords detected")

    pattern = re.compile(rule["id_pattern"], re.IGNORECASE)
    match = pattern.search(raw_text or "")
    id_score = 60 if match else 0
    extracted_id = match.group(0).replace(" ", "") if match else None
    if extracted_id:
        reasons.append("Detected valid document number pattern")
    else:
        reasons.append("Document number pattern not detected")

    confidence = min(100, keyword_score + id_score)
    verified = confidence >= 60

    return {
        "verified": verified,
        "confidence": confidence,
        "reasons": reasons,
        "extracted_id": extracted_id,
    }
