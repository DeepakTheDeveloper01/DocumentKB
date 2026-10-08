from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from .document_loader import DocumentChunk

TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_]+")
STOPWORDS_MEM = {
    "the", "a", "an", "and", "or", "but", "if", "is", "are", "was", "were",
    "be", "been", "being", "have", "has", "had", "do", "does", "did", "will",
    "would", "could", "should", "may", "might", "can", "to", "of", "in", "on",
    "at", "by", "for", "with", "about", "this", "that", "these", "those",
    "it", "its", "from", "they", "them", "their", "we", "our", "you", "your",
    "i", "me", "my", "what", "which", "who", "whom", "how", "where", "when",
    "why", "there", "here", "not", "so", "as", "very", "too", "than", "just",
    "also", "only", "same", "own", "some", "other", "most", "more", "each",
    "all", "every", "both", "few", "into", "through", "before", "after",
    "above", "below", "under", "over", "between", "against", "please",
    "help", "question", "answer", "thanks", "thank", "want", "need",
    "know", "tell", "give", "ask", "explain", "me", "tell", "let", "make",
    "get", "say", "see", "use", "using", "used", "section", "see", "okay",
    "ok", "thanks", "bye", "hello", "hi", "hey", "now", "alright", "right",
}


def _tokens(text: str) -> List[str]:
    return [t.lower() for t in TOKEN_RE.findall(text) if t.lower() not in STOPWORDS_MEM and len(t) > 1]


TOPIC_KEYWORDS = {
    "billing": {"billing", "bill", "price", "pricing", "invoice", "invoices", "payment", "payments", "refund", "refunds", "credit", "credits", "charge", "charges", "overage", "cost", "plan", "plans", "tier", "tiers", "subscription", "subscriptions", "tax", "vat", "gst", "card", "cards", "dollars", "monthly", "usd", "declined", "wallet", "storage", "pro", "starter", "enterprise", "free", "trial", "prorated", "prorate", "addon", "included"},
    "account": {"account", "accounts", "signup", "sign", "signin", "register", "registration", "login", "logins", "logged", "password", "passwords", "email", "emails", "verify", "verified", "verification", "reset", "credentials", "user", "users", "profile", "sso", "saml", "oidc", "provision"},
    "api": {"api", "apis", "key", "keys", "token", "tokens", "endpoint", "endpoints", "rate", "rates", "limit", "limits", "429", "curl", "http", "https", "header", "headers", "authorization", "authentication", "authenticate", "auth", "bearer", "webhook", "webhooks", "secret", "secrets", "rest", "signature", "signatures", "hmac", "event", "events", "payload", "payloads", "callback", "callbacks", "idempotency", "methods"},
    "cli": {"cli", "command", "commands", "terminal", "terminals", "install", "installation", "brew", "homebrew", "winget", "powershell", "bash", "shell", "shells", "login", "device", "localhost", "port", "completion", "tab"},
    "teams": {"team", "teams", "member", "members", "role", "roles", "rbac", "permission", "permissions", "access", "invite", "invites", "invited", "invitation", "admin", "admins", "owner", "owners", "developer", "developers", "viewer", "viewers", "offboard", "offboarding", "remove", "removed", "removal", "organization", "organizations", "group", "groups"},
    "deployment": {"deploy", "deploys", "deployment", "deployments", "build", "builds", "building", "runtime", "runtimes", "error", "errors", "failure", "failures", "fail", "fails", "failed", "crash", "crashes", "health", "check", "checks", "memory", "outofmemory", "oom", "log", "logs", "logging", "instance", "instances", "port", "ports", "container", "containers"},
    "troubleshooting": {"trouble", "troubleshoot", "troubleshooting", "issue", "issues", "problem", "problems", "bug", "bugs", "fix", "fixed", "fixing", "broken", "contact", "faq", "faqs", "help", "stuck", "unexpected", "failing", "debug", "debugging"},
    "getting_started": {"start", "started", "starting", "first", "create", "created", "creating", "project", "projects", "setup", "set", "guide", "guides", "tutorial", "tutorials", "welcome", "begin", "beginner", "beginning", "onboard", "onboarding", "region", "regions", "repo", "repos", "repository", "repositories"},
}


def _detect_topic(text: str, current_topic: Optional[str] = None) -> Optional[str]:
    toks_list = _tokens(text)
    toks_set = set(toks_list)
    tok_freq = Counter(toks_list)
    scores: Dict[str, float] = {}
    for topic, keys in TOPIC_KEYWORDS.items():
        overlap_tokens = toks_set & keys
        if not overlap_tokens:
            continue
        count = len(overlap_tokens)
        freq_weighted = count + sum(tok_freq.get(tok, 0) * 0.25 for tok in overlap_tokens)
        length_weighted = sum(len(tok) / 10.0 for tok in overlap_tokens)
        scores[topic] = freq_weighted + length_weighted
        if current_topic and topic == current_topic:
            scores[topic] += 2.8
    if not scores:
        return None
    return max(scores.items(), key=lambda x: x[1])[0]


@dataclass
class Turn:
    turn_index: int
    user_query: str
    assistant_response: str
    citations_used: List[str] = field(default_factory=list)
    topic: Optional[str] = None
    response_key_points: List[str] = field(default_factory=list)
    user_topic: Optional[str] = None


@dataclass
class TopicSummary:
    name: str
    turns: List[int]
    key_points: List[str]
    covered_sections: Set[str]


class ConversationMemory:
    def __init__(self):
        self.turns: List[Turn] = []
        self.current_topic: Optional[str] = None
        self.topic_history: List[TopicSummary] = []
        self._covered_section_keys: Dict[str, List[int]] = defaultdict(list)
        self._response_fragments: Set[str] = set()
        self._user_terms_per_turn: List[Counter] = []

    def _add_response_fragments(self, text: str) -> None:
        sentences = re.split(r"[.!?]+", text)
        for s in sentences:
            stripped = s.strip().lower()
            if 15 < len(stripped) < 200:
                self._response_fragments.add(stripped)

    def find_repeated_fragment(self, candidate_text: str) -> Optional[str]:
        cand_sentences = re.split(r"[.!?]+", candidate_text)
        for cs in cand_sentences:
            cs_norm = cs.strip().lower()
            if len(cs_norm) < 15:
                continue
            for existing in self._response_fragments:
                if len(existing) < 15:
                    continue
                words1 = cs_norm.split()
                words2 = existing.split()
                if len(words1) < 5 or len(words2) < 5:
                    continue
                s1 = set(words1)
                s2 = set(words2)
                overlap = len(s1 & s2) / min(len(s1), len(s2))
                if overlap >= 0.75:
                    return existing[:80]
        return None

    def get_context_hints(self) -> List[str]:
        hints: List[str] = []
        if self.current_topic:
            hints.append(self.current_topic)
        N = min(3, len(self.turns))
        for i in range(len(self.turns) - N, len(self.turns)):
            t = self.turns[i]
            hints.append(t.user_query)
        recent_terms = Counter()
        for c in self._user_terms_per_turn[-3:]:
            recent_terms.update(c)
        for term, _ in recent_terms.most_common(8):
            hints.append(term)
        return hints

    def get_avoid_sections(self) -> List[str]:
        avoid: List[str] = []
        for sec_key, turn_idxs in self._covered_section_keys.items():
            if len(turn_idxs) >= 2:
                avoid.append(sec_key)
        return avoid

    EXPLICIT_SWITCH_PHRASES = [
        "actually let's talk about", "actually, let's talk about",
        "let's talk about", "let's discuss",
        "back to", "going back to", "returning to",
        "moving on to", "switching to",
        "instead of that", "instead",
        "how about", "what about",
        "one more thing about",
        "last question",
    ]

    FOLLOW_UP_SIGNALS = [
        "specifically", "more details", "tell me more",
        "what if", "what about", "how do",
        "how many", "how much", "how long",
        "how often", "explain that", "expand on",
        "included", "include", "does that",
        "okay,", "ok,", "okay ", "ok ",
    ]

    def is_topic_switch(self, user_query: str) -> tuple[bool, Optional[str], Optional[str]]:
        q_lower = user_query.lower()
        new_topic = _detect_topic(user_query, current_topic=None)
        old_topic = self.current_topic
        if old_topic is None or new_topic is None:
            return False, old_topic, new_topic

        has_explicit_switch = any(p in q_lower for p in self.EXPLICIT_SWITCH_PHRASES)
        has_follow_up = any(p in q_lower for p in self.FOLLOW_UP_SIGNALS)

        if old_topic != new_topic:
            strong_terms = TOPIC_KEYWORDS.get(new_topic, set())
            q_tokens = set(_tokens(user_query))
            overlap_new = len(q_tokens & strong_terms)
            strong_old = TOPIC_KEYWORDS.get(old_topic, set())
            overlap_old = len(q_tokens & strong_old)

            if has_explicit_switch and overlap_new >= 1:
                return True, old_topic, new_topic

            if has_follow_up and not has_explicit_switch:
                return False, old_topic, new_topic

            margin = 2
            if overlap_new >= 1 and overlap_new > overlap_old + margin:
                return True, old_topic, new_topic

            if overlap_new >= 1 and overlap_old == 0:
                return True, old_topic, new_topic

        return False, old_topic, new_topic

    def prior_answer_on_topic(self, topic: Optional[str]) -> Optional[str]:
        if not topic:
            return None
        topic_turns = [t for t in self.turns if t.topic == topic]
        if not topic_turns:
            return None
        points: List[str] = []
        for t in topic_turns:
            points.extend(t.response_key_points)
        if points:
            return "Earlier we already discussed " + topic + ". Previously covered: " + "; ".join(points[:4]) + "."
        return None

    def record_turn(
        self,
        user_query: str,
        assistant_response: str,
        citations_used: List[DocumentChunk],
        key_points: List[str],
    ) -> Turn:
        user_tokens = Counter(_tokens(user_query))
        self._user_terms_per_turn.append(user_tokens)
        topic = _detect_topic(user_query, current_topic=self.current_topic) or self.current_topic
        turn_idx = len(self.turns)
        citation_sec_keys = [f"{c.doc_path}::{c.section_number}" for c in citations_used]
        for key in citation_sec_keys:
            self._covered_section_keys[key].append(turn_idx)
        self._add_response_fragments(assistant_response)
        turn = Turn(
            turn_index=turn_idx,
            user_query=user_query,
            assistant_response=assistant_response,
            citations_used=citation_sec_keys,
            topic=topic,
            response_key_points=key_points,
            user_topic=topic,
        )
        self.turns.append(turn)
        if topic and topic != self.current_topic:
            self.current_topic = topic
        return turn

    def summarise_so_far(self) -> str:
        if not self.turns:
            return "No prior conversation."
        parts = [f"We've had {len(self.turns)} turn(s) so far."]
        grouped: Dict[str, List[Turn]] = defaultdict(list)
        for t in self.turns:
            grouped[t.topic or "general"].append(t)
        for topic, turns in grouped.items():
            t_count = len(turns)
            sections = set()
            for t in turns:
                for c in t.citations_used:
                    sections.add(c.split("::")[-1])
            parts.append(f"Topic '{topic}': {t_count} turn(s), citing sections {sorted(sections)}.")
        return " ".join(parts)
