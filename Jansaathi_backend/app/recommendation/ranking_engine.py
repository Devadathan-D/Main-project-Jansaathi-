from app.models.user import User
from app.models.scheme import Scheme

def calculate_score(user: User, scheme: Scheme) -> float:
    """
    Calculate a ranking score for an eligible scheme.
    Returns a float between 0.0 and 100.0.
    
    Scoring Breakdown:
    - Age match:          15 pts
    - Income match:       25 pts
    - State match:        15 pts
    - Occupation match:   15 pts
    - Category match:     10 pts
    - Document match:     20 pts (proportional)
    """

    def _as_list(value):
        if not value:
            return []
        if isinstance(value, list):
            return [str(v).strip().lower() for v in value if str(v).strip()]
        if isinstance(value, str):
            return [v.strip().lower() for v in value.split(",") if v.strip()]
        return [str(value).strip().lower()]

    score = 0.0

    # ---------- 1. AGE MATCH (15 pts) ----------
    if user.age is not None:
        min_ok = scheme.min_age is None or user.age >= scheme.min_age
        max_ok = scheme.max_age is None or user.age <= scheme.max_age
        if min_ok and max_ok:
            score += 15.0

    # ---------- 2. INCOME MATCH (25 pts) ----------
    if user.income is not None:
        min_ok = scheme.min_income is None or user.income >= scheme.min_income
        max_ok = scheme.max_income is None or user.income <= scheme.max_income
        if min_ok and max_ok:
            score += 25.0
        elif scheme.min_income is not None and scheme.max_income is not None:
            # Partial credit for near misses to reduce abrupt cutoffs.
            band = max(scheme.max_income - scheme.min_income, 1.0)
            if user.income < scheme.min_income:
                distance = scheme.min_income - user.income
            else:
                distance = user.income - scheme.max_income
            penalty = min(distance / band, 1.0)
            score += 25.0 * (1.0 - penalty) * 0.4

    # ---------- 3. STATE MATCH (15 pts) ----------
    if scheme.state:
        if scheme.state.upper() == "ALL":
            score += 8.0
        elif user.state and scheme.state.lower() == user.state.lower():
            score += 15.0

    # ---------- 4. OCCUPATION MATCH (15 pts) ----------
    if scheme.occupation and user.occupation:
        if scheme.occupation.lower() == user.occupation.lower():
            score += 15.0

    # ---------- 5. CATEGORY MATCH (10 pts) ----------
    if scheme.category and user.category:
        if scheme.category.lower() == user.category.lower():
            score += 10.0

    # ---------- 6. DOCUMENT MATCH (20 pts) ----------
    required_docs = _as_list(scheme.required_documents)
    user_docs = set(_as_list(user.documents))
    if required_docs:
        matched = len(set(required_docs).intersection(user_docs))
        total = len(required_docs)
        if total > 0:
            score += (matched / total) * 20.0
    else:
        # No document barrier gives a small boost.
        score += 5.0

    return round(min(score, 100.0), 2)
