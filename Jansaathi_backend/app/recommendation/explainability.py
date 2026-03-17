from typing import List
from app.models.user import User
from app.models.scheme import Scheme

def build_explanation(user: User, scheme: Scheme) -> List[str]:
    """
    Build a human-readable explanation for why a scheme was recommended.
    This helps the user understand the eligibility logic.
    """

    reasons = []

    # ---------- AGE ----------
    if user.age:
        if scheme.min_age and user.age >= scheme.min_age:
            reasons.append(f"Meets minimum age requirement ({scheme.min_age}+)")
        if scheme.max_age and user.age <= scheme.max_age:
            reasons.append(f"Within maximum age limit ({scheme.max_age})")

    # ---------- INCOME ----------
    # We handle different scenarios: Range, Max Only, or Min Only
    if user.income:
        if scheme.min_income and scheme.max_income:
            if scheme.min_income <= user.income <= scheme.max_income:
                reasons.append(f"Income within eligible range (₹{scheme.min_income} - ₹{scheme.max_income})")
        elif scheme.max_income:
            # Handle schemes with only an upper limit (e.g., BPL cards)
            if user.income <= scheme.max_income:
                reasons.append(f"Income below maximum limit (₹{scheme.max_income})")
        elif scheme.min_income:
            # Handle schemes with only a lower limit (e.g., Tax schemes)
            if user.income >= scheme.min_income:
                reasons.append(f"Income above minimum threshold (₹{scheme.min_income})")

    # ---------- STATE ----------
    if user.state and scheme.state:
        if scheme.state.upper() == "ALL":
            reasons.append("Available nationwide")
        elif scheme.state.lower() == user.state.lower():
            reasons.append(f"Resident of {user.state}")

    # ---------- OCCUPATION ----------
    if user.occupation and scheme.occupation:
        if scheme.occupation.lower() == user.occupation.lower():
            reasons.append(f"Applicable for {user.occupation}s")

    # ---------- CATEGORY ----------
    if user.category and scheme.category:
        if scheme.category.lower() == user.category.lower():
            reasons.append(f"Eligible under {user.category} category")

    # ---------- DOCUMENTS ----------
    if scheme.required_documents:
        required_docs = scheme.required_documents

        # Normalize to list in case data is a string
        if isinstance(required_docs, str):
            required_docs = [doc.strip() for doc in required_docs.split(",")]

        user_docs = user.documents if user.documents else []
        matched_docs = set(required_docs).intersection(set(user_docs))

        if matched_docs:
            count = len(matched_docs)
            total = len(required_docs)
            reasons.append(f"You already have {count} of the {total} required documents")

    return reasons