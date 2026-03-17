from collections import defaultdict
from typing import Any, Dict, List, Tuple

from app.extensions import db
from app.models.scheme import Scheme
from app.models.user import User

from .explainability import build_explanation
from .ranking_engine import calculate_score
from .rule_engine import is_eligible


class ContentRecommender:
    """
    Hybrid recommendation engine:
    - content signal from user-to-scheme matching
    - collaborative signal from similar users
    - popularity signal as cold-start fallback
    """

    def __init__(self):
        self.content_weight = 0.65
        self.collaborative_weight = 0.25
        self.popularity_weight = 0.10
        self.similarity_threshold = 0.20
        self.max_neighbors = 25

    def recommend(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        user = db.session.get(User, user_id)
        if not user:
            return []

        schemes = Scheme.query.filter_by(is_active=True).all()
        if not schemes:
            return []

        other_users = User.query.filter(User.id != user_id).all()

        # Candidate schemes: apply hard mismatch checks but do not reject for
        # missing profile fields or missing documents.
        candidates = [
            scheme
            for scheme in schemes
            if is_eligible(
                user,
                scheme,
                strict_documents=False,
                allow_missing_profile=True,
            )
        ]

        # If hard filters leave nothing, recover with all active schemes.
        if not candidates:
            candidates = schemes

        content_scores = {scheme.id: calculate_score(user, scheme) for scheme in candidates}
        collaborative_scores = self._collaborative_scores(user, candidates, other_users)
        popularity_scores = self._popularity_scores(candidates, other_users)

        recommendations = []
        for scheme in candidates:
            content_score = content_scores.get(scheme.id, 0.0)
            collaborative_score = collaborative_scores.get(scheme.id, 0.0)
            popularity_score = popularity_scores.get(scheme.id, 0.0)

            final_score = (
                self.content_weight * content_score
                + self.collaborative_weight * collaborative_score
                + self.popularity_weight * popularity_score
            )

            reasons = build_explanation(user, scheme)
            if collaborative_score >= 20:
                reasons.append("Recommended based on similar user profiles")
            if popularity_score >= 30:
                reasons.append("Widely relevant across users")

            recommendations.append(
                {
                    "id": scheme.id,
                    "name": scheme.name,
                    "description": scheme.description,
                    "link": scheme.link,
                    "score": round(min(final_score, 100.0), 2),
                    "reasons": reasons,
                    "required_documents": scheme.required_documents,
                    "score_breakdown": {
                        "content": round(content_score, 2),
                        "collaborative": round(collaborative_score, 2),
                        "popularity": round(popularity_score, 2),
                    },
                }
            )

        recommendations.sort(key=lambda x: x["score"], reverse=True)
        return recommendations[:limit]

    def _collaborative_scores(
        self,
        target_user: User,
        schemes: List[Scheme],
        other_users: List[User],
    ) -> Dict[int, float]:
        neighbors: List[Tuple[User, float]] = []
        for other in other_users:
            sim = self._user_similarity(target_user, other)
            if sim >= self.similarity_threshold:
                neighbors.append((other, sim))

        if not neighbors:
            return {}

        neighbors.sort(key=lambda item: item[1], reverse=True)
        neighbors = neighbors[: self.max_neighbors]

        weighted_sum = defaultdict(float)
        weight_total = defaultdict(float)

        for neighbor, sim in neighbors:
            for scheme in schemes:
                if not is_eligible(
                    neighbor,
                    scheme,
                    strict_documents=False,
                    allow_missing_profile=True,
                ):
                    continue

                neighbor_affinity = calculate_score(neighbor, scheme) / 100.0
                weighted_sum[scheme.id] += sim * neighbor_affinity
                weight_total[scheme.id] += sim

        scores = {}
        for scheme in schemes:
            if weight_total[scheme.id] > 0:
                scores[scheme.id] = (weighted_sum[scheme.id] / weight_total[scheme.id]) * 100.0
        return scores

    def _popularity_scores(
        self,
        schemes: List[Scheme],
        users: List[User],
    ) -> Dict[int, float]:
        if not users:
            return {}

        eligible_counts = defaultdict(int)
        for user in users:
            for scheme in schemes:
                if is_eligible(
                    user,
                    scheme,
                    strict_documents=False,
                    allow_missing_profile=True,
                ):
                    eligible_counts[scheme.id] += 1

        total_users = max(len(users), 1)
        return {
            scheme.id: (eligible_counts[scheme.id] / total_users) * 100.0
            for scheme in schemes
        }

    def _user_similarity(self, user_a: User, user_b: User) -> float:
        parts: List[Tuple[float, float]] = []

        # Age similarity
        if user_a.age is not None and user_b.age is not None:
            age_delta = abs(user_a.age - user_b.age)
            age_sim = max(0.0, 1.0 - min(age_delta / 40.0, 1.0))
            parts.append((age_sim, 0.25))

        # Income similarity
        if user_a.income is not None and user_b.income is not None:
            denom = max(user_a.income, user_b.income, 1.0)
            income_sim = max(0.0, 1.0 - min(abs(user_a.income - user_b.income) / denom, 1.0))
            parts.append((income_sim, 0.30))

        # Categorical similarities
        for attr, weight in (("state", 0.15), ("occupation", 0.15), ("category", 0.10)):
            a = getattr(user_a, attr, None)
            b = getattr(user_b, attr, None)
            if a and b:
                parts.append((1.0 if str(a).lower() == str(b).lower() else 0.0, weight))

        # Document overlap (Jaccard)
        docs_a = self._normalized_set(user_a.documents)
        docs_b = self._normalized_set(user_b.documents)
        if docs_a and docs_b:
            inter = len(docs_a.intersection(docs_b))
            union = len(docs_a.union(docs_b))
            parts.append(((inter / union) if union else 0.0, 0.05))

        if not parts:
            return 0.0

        weighted_score = sum(score * weight for score, weight in parts)
        total_weight = sum(weight for _, weight in parts)
        return weighted_score / total_weight if total_weight else 0.0

    def _normalized_set(self, value: Any) -> set:
        if not value:
            return set()
        if isinstance(value, list):
            return {str(v).strip().lower() for v in value if str(v).strip()}
        if isinstance(value, str):
            return {v.strip().lower() for v in value.split(",") if v.strip()}
        return {str(value).strip().lower()}
