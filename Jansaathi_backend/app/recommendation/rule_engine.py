from app.models.user import User
from app.models.scheme import Scheme

def _as_list(value):
    if not value:
        return []
    if isinstance(value, list):
        return [str(v).strip().lower() for v in value if str(v).strip()]
    if isinstance(value, str):
        return [v.strip().lower() for v in value.split(",") if v.strip()]
    return [str(value).strip().lower()]


def is_eligible(
    user: User,
    scheme: Scheme,
    strict_documents: bool = False,
    allow_missing_profile: bool = True,
) -> bool:
    """
    Determine whether a user is strictly eligible for a scheme.
    Returns False if ANY criteria is not met.
    """
    
    # ---------- AGE CHECK ----------
    if scheme.min_age is not None:
        if user.age is None:
            if not allow_missing_profile:
                return False
        elif user.age < scheme.min_age:
            return False

    if scheme.max_age is not None:
        if user.age is None:
            if not allow_missing_profile:
                return False
        elif user.age > scheme.max_age:
            return False

    # ---------- INCOME CHECK ----------
    if scheme.min_income is not None:
        if user.income is None:
            if not allow_missing_profile:
                return False
        elif user.income < scheme.min_income:
            return False

    if scheme.max_income is not None:
        if user.income is None:
            if not allow_missing_profile:
                return False
        elif user.income > scheme.max_income:
            return False

    # ---------- STATE CHECK ----------
    if scheme.state and scheme.state.upper() != "ALL":
        if user.state:
            if scheme.state.lower() != user.state.lower():
                return False
        elif not allow_missing_profile:
            return False

    # ---------- OCCUPATION CHECK ----------
    if scheme.occupation:
        if user.occupation:
            if scheme.occupation.lower() != user.occupation.lower():
                return False
        elif not allow_missing_profile:
            return False

    # ---------- CATEGORY CHECK ----------
    if scheme.category:
        if user.category:
            if scheme.category.lower() != user.category.lower():
                return False
        elif not allow_missing_profile:
            return False

    # ---------- DOCUMENT CHECK ----------
    # Documents are soft constraints by default, because users can still apply
    # after uploading missing documents.
    if strict_documents and scheme.required_documents:
        required_docs = set(_as_list(scheme.required_documents))
        user_docs = set(_as_list(user.documents))
        if required_docs and not required_docs.issubset(user_docs):
            return False

    return True
