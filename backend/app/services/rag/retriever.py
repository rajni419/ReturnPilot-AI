"""
RAG Policy Retriever for ReturnPilot AI.
Provides vector-based policy retrieval, relevance thresholding, and source citations.
"""

import math
import re
from typing import Dict, List, Optional, Set, Tuple
from pydantic import BaseModel, Field

from .policy_store import PolicySection, policy_store


class PolicyCitation(BaseModel):
    policy_id: str
    section: str
    title: str
    category: str
    snippet: str
    similarity_score: float
    allowed_actions: List[str] = Field(default_factory=list)


class RetrievalResult(BaseModel):
    query: str
    citations: List[PolicyCitation]
    is_relevant: bool
    insufficient_evidence: bool = False
    suggested_actions: List[str] = Field(default_factory=list)


# Hinglish and Hindi term expansions for semantic bridging
MULTILINGUAL_EXPANSIONS: Dict[str, List[str]] = {
    # Returns & Refunds
    "paisa": ["refund", "money", "timeline", "bank"],
    "paise": ["refund", "money", "timeline", "bank"],
    "wapas": ["return", "refund", "pickup"],
    "waapas": ["return", "refund", "pickup"],
    "lautana": ["return", "refund"],
    "return": ["return", "policy", "window"],
    "refund": ["refund", "timeline", "bank", "account"],
    # Exchange & Size
    "size": ["size", "apparel", "shoes", "exchange"],
    "chhota": ["size", "shoes", "apparel", "exchange"],
    "chota": ["size", "shoes", "apparel", "exchange"],
    "bada": ["size", "shoes", "apparel", "exchange"],
    "fit": ["size", "apparel", "exchange"],
    "tight": ["size", "exchange", "apparel"],
    "loose": ["size", "exchange", "apparel"],
    "exchange": ["exchange", "size", "apparel", "footwear"],
    "badalna": ["exchange", "replace"],
    "badal": ["exchange", "replace"],
    # Damage & Defect
    "toota": ["damaged", "broken", "defective"],
    "tuta": ["damaged", "broken", "defective"],
    "kharab": ["defective", "electronics", "broken", "damaged"],
    "damaged": ["damaged", "broken", "defective", "photo"],
    "damage": ["damaged", "broken", "defective", "photo"],
    "broken": ["damaged", "broken", "defective"],
    "defective": ["defective", "electronics", "broken"],
    "working": ["defective", "electronics", "repair"],
    "leaking": ["beauty", "cosmetics", "damaged"],
    # Wrong Item
    "galat": ["wrong", "different", "tampered"],
    "different": ["wrong", "different", "tampered"],
    "wrong": ["wrong", "different", "tampered"],
    # Pickup & Courier
    "pickup": ["pickup", "courier", "doorstep", "address"],
    "courier": ["pickup", "courier", "doorstep"],
    "aayega": ["pickup", "delivery", "timeline"],
    "kab": ["timeline", "pickup", "refund"],
    # Policy
    "policy": ["policy", "rules", "window", "days"],
    "niyam": ["policy", "rules"],
    "shartein": ["policy", "conditions"],
}


STOPWORDS: Set[str] = {
    "a", "an", "the", "and", "or", "in", "on", "at", "to", "for", "of", "with",
    "is", "are", "was", "were", "be", "been", "being", "have", "has", "had",
    "do", "does", "did", "i", "you", "he", "she", "it", "we", "they", "my", "your",
    "our", "their", "this", "that", "these", "those", "how", "what", "which", "who",
    "whom", "why", "can", "could", "should", "would", "may", "might", "must",
}


def tokenize(text: str) -> List[str]:
    """Extracts alphanumeric tokens in lowercase, excluding common stop words."""
    tokens = re.findall(r"\b[a-zA-Z0-9_\u0900-\u097F]+\b", text.lower())
    return [t for t in tokens if t not in STOPWORDS or len(t) > 4]



class PolicyVectorRetriever:
    """
    In-memory hybrid dense-sparse vector retriever for policy documents.
    Supports English, Hindi, and Hinglish queries with cosine similarity scoring.
    """

    def __init__(self, store=policy_store):
        self.store = store
        self._doc_vectors: Dict[str, Dict[str, float]] = {}
        self._idf: Dict[str, float] = {}
        self._doc_lengths: Dict[str, float] = {}
        self._reindex()

    def _reindex(self) -> None:
        """Computes TF-IDF index across all policy sections."""
        policies = self.store.get_all()
        doc_count = len(policies)
        if doc_count == 0:
            return

        df: Dict[str, int] = {}
        term_freqs: Dict[str, Dict[str, int]] = {}

        for p in policies:
            # Aggregate title, content, and keywords
            text = f"{p.title} {p.category} {p.content} {' '.join(p.keywords)}"
            tokens = tokenize(text)
            tf: Dict[str, int] = {}
            for t in tokens:
                tf[t] = tf.get(t, 0) + 1
            term_freqs[p.policy_id] = tf
            for t in set(tokens):
                df[t] = df.get(t, 0) + 1

        # Calculate IDF with smoothing
        self._idf = {
            term: math.log(1.0 + (doc_count / (count + 0.5))) + 1.0
            for term, count in df.items()
        }

        # Calculate normalized TF-IDF document vectors
        self._doc_vectors = {}
        for p in policies:
            tf = term_freqs.get(p.policy_id, {})
            vec: Dict[str, float] = {}
            norm_sq = 0.0
            for term, count in tf.items():
                tfidf = (1.0 + math.log(count)) * self._idf.get(term, 1.0)
                # Boost keyword terms
                if term in [k.lower() for k in p.keywords]:
                    tfidf *= 1.8
                vec[term] = tfidf
                norm_sq += tfidf * tfidf

            norm = math.sqrt(norm_sq) if norm_sq > 0 else 1.0
            self._doc_vectors[p.policy_id] = {t: w / norm for t, w in vec.items()}
            self._doc_lengths[p.policy_id] = norm

    def retrieve(
        self,
        query: str,
        top_k: int = 3,
        min_relevance_score: float = 0.12,
    ) -> RetrievalResult:
        """
        Retrieves top relevant policy chunks for a query.
        Handles Hinglish/Hindi expansion and enforces relevance thresholding.
        """
        raw_tokens = tokenize(query)
        if not raw_tokens:
            return RetrievalResult(
                query=query,
                citations=[],
                is_relevant=False,
                insufficient_evidence=True,
            )

        # Expand query with Hinglish/Hindi domain synonyms
        expanded_tokens: Set[str] = set(raw_tokens)
        for token in raw_tokens:
            if token in MULTILINGUAL_EXPANSIONS:
                for exp in MULTILINGUAL_EXPANSIONS[token]:
                    expanded_tokens.add(exp)

        # Compute query vector
        query_tf: Dict[str, int] = {}
        for t in expanded_tokens:
            query_tf[t] = query_tf.get(t, 0) + 1

        query_vec: Dict[str, float] = {}
        query_norm_sq = 0.0
        for term, count in query_tf.items():
            idf = self._idf.get(term, 1.0)
            weight = (1.0 + math.log(count)) * idf
            query_vec[term] = weight
            query_norm_sq += weight * weight

        query_norm = math.sqrt(query_norm_sq) if query_norm_sq > 0 else 1.0
        query_normalized = {t: w / query_norm for t, w in query_vec.items()}

        # Compute cosine similarity with all policy documents
        scored_policies: List[Tuple[float, PolicySection]] = []
        for p in self.store.get_all():
            doc_vec = self._doc_vectors.get(p.policy_id, {})
            score = sum(query_normalized.get(t, 0.0) * doc_vec.get(t, 0.0) for t in query_normalized if t in doc_vec)

            # Extra boost if query matches policy category directly
            if any(t in p.category.lower() for t in raw_tokens):
                score += 0.08

            if score > 0.0:
                scored_policies.append((score, p))

        scored_policies.sort(key=lambda x: x[0], reverse=True)

        # Evaluate against threshold
        citations: List[PolicyCitation] = []
        suggested_actions: Set[str] = set()

        for score, p in scored_policies[:top_k]:
            if score >= min_relevance_score:
                snippet = p.content[:220] + ("..." if len(p.content) > 220 else "")
                citations.append(
                    PolicyCitation(
                        policy_id=p.policy_id,
                        section=p.section,
                        title=p.title,
                        category=p.category,
                        snippet=snippet,
                        similarity_score=round(score, 3),
                        allowed_actions=p.allowed_actions,
                    )
                )
                for action in p.allowed_actions:
                    suggested_actions.add(action)

        if not citations:
            return RetrievalResult(
                query=query,
                citations=[],
                is_relevant=False,
                insufficient_evidence=True,
                suggested_actions=[],
            )

        return RetrievalResult(
            query=query,
            citations=citations,
            is_relevant=True,
            insufficient_evidence=False,
            suggested_actions=list(suggested_actions),
        )


# Global retriever instance
retriever = PolicyVectorRetriever()
