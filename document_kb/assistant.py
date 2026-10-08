from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from .conversation_memory import ConversationMemory, TOPIC_KEYWORDS
from .document_loader import DocumentChunk, load_knowledge_base
from .retrieval import RetrievalEngine, RetrievalResult

try:
    from dotenv import load_dotenv  # type: ignore

    load_dotenv()
except Exception:
    pass

OPENAI_KEY = os.environ.get("GROQ_API_KEY")
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY")
USE_REAL_LLM = bool(OPENAI_KEY or ANTHROPIC_KEY)


def _citation_label(chunk: DocumentChunk) -> str:
    base = f"[{chunk.doc_title}"
    if chunk.section_number:
        base += f" §{chunk.section_number}"
    if chunk.section_title:
        base += f" {chunk.section_title!r}"
    base += "]"
    return base


@dataclass
class AssistantResponse:
    text: str
    citations: List[DocumentChunk]
    key_points: List[str]
    topic: Optional[str]
    is_topic_switch: bool
    avoided_repetition: bool
    note: Optional[str] = None


class KnowledgeAssistant:
    def __init__(self, kb_dir: Optional[str | Path] = None):
        base = Path(kb_dir) if kb_dir else Path(__file__).parent.parent / "knowledge_base"
        self.kb_dir = base
        self.chunks = load_knowledge_base(base)
        self.retriever = RetrievalEngine(self.chunks)
        self.memory = ConversationMemory()

    def reset(self) -> None:
        self.memory = ConversationMemory()

    def _synthesize_demo(self, query: str, hits: List[RetrievalResult]) -> Tuple[str, List[str], List[DocumentChunk]]:
        if not hits:
            return (
                "I don't have information in the knowledge base that directly addresses your question. "
                "Could you rephrase or try a different angle? I cover getting started, billing, API/auth, "
                "teams/permissions, and troubleshooting for the AcmeCloud platform.",
                [],
                [],
            )

        top_score = max(h.score for h in hits) if hits else 0.0
        quality_threshold = max(0.25 * top_score, 1.0)

        used_chunks: List[DocumentChunk] = []
        key_points: List[str] = []
        fragments: List[str] = []
        seen_keys = set()

        for i, hit in enumerate(hits):
            if len(used_chunks) >= 3:
                break
            if hit.score < quality_threshold and used_chunks:
                continue
            chunk = hit.chunk
            key = (chunk.doc_path, chunk.section_number)
            if key in seen_keys:
                continue
            seen_keys.add(key)
            if hit.score < quality_threshold and len(hit.matched_terms) < 2:
                continue
            used_chunks.append(chunk)
            label = _citation_label(chunk)
            text = chunk.text.strip()
            clean = " ".join(text.split())
            if len(clean) > 260:
                sentences = clean.split(". ")
                head = ". ".join(sentences[:3])
                if not head.endswith("."):
                    head += "."
                fragment = head
            else:
                fragment = clean
                if not fragment.endswith("."):
                    fragment += "."
            fragments.append(fragment + " " + label)
            title_snippet = f"{chunk.section_title or chunk.doc_title}"
            key_points.append(f"{title_snippet} ({_citation_label(chunk)})")

        if not used_chunks:
            chunk = hits[0].chunk
            used_chunks.append(chunk)
            label = _citation_label(chunk)
            clean = " ".join(chunk.text.strip().split())
            if len(clean) > 260:
                sentences = clean.split(". ")
                clean = ". ".join(sentences[:3]) + ("." if not clean.endswith(".") else "")
            fragments.append(clean + " " + label)
            key_points.append(f"{chunk.section_title or chunk.doc_title} ({label})")

        intro = self._build_intro(query, used_chunks[0])
        body = " ".join(fragments)
        final = intro + " " + body if intro else body
        return final, key_points, used_chunks

    def _build_intro(self, query: str, top_chunk: DocumentChunk) -> str:
        q = query.lower()
        title = top_chunk.section_title or top_chunk.doc_title
        section = top_chunk.section_number or ""

        intro_variants = [
            f"Based on the {title} section{f' (§{section})' if section else ''}, here is what I found:",
            f"For your question about {self._extract_subject(q)}, the documentation states:",
            f"Looking at {title}, the relevant guidance is:",
            f"Here is the information from the knowledge base on this topic:",
        ]
        return intro_variants[hash(q) % len(intro_variants)]

    def _extract_subject(self, q_lower: str) -> str:
        keywords = []
        if "invoice" in q_lower or "bill" in q_lower or "charge" in q_lower:
            keywords.append("billing")
        if "api" in q_lower or "key" in q_lower or "auth" in q_lower:
            keywords.append("API authentication")
        if "team" in q_lower or "role" in q_lower or "member" in q_lower or "permission" in q_lower:
            keywords.append("team permissions")
        if "deploy" in q_lower or "build" in q_lower or "error" in q_lower:
            keywords.append("deployments")
        if "login" in q_lower or "sign" in q_lower or "account" in q_lower or "sso" in q_lower:
            keywords.append("account access")
        if "cli" in q_lower or "install" in q_lower:
            keywords.append("CLI setup")
        if "refund" in q_lower or "credit" in q_lower:
            keywords.append("refunds/credits")
        if "price" in q_lower or "plan" in q_lower or "tier" in q_lower:
            keywords.append("pricing tiers")
        return ", ".join(keywords) if keywords else "this"

    def _synthesize_real_llm(self, query: str, hits: List[RetrievalResult]) -> Tuple[str, List[str], List[DocumentChunk]]:
        if not hits:
            return (
                "I don't have information in the knowledge base that directly addresses your question. "
                "Could you rephrase or try a different angle?",
                [],
                [],
            )
        context_parts: List[str] = []
        used_chunks: List[DocumentChunk] = []
        for i, hit in enumerate(hits[:4]):
            c = hit.chunk
            used_chunks.append(c)
            label = _citation_label(c)
            context_parts.append(f"SOURCE {i+1} {label}:\n{c.text}")

        context = "\n\n".join(context_parts)
        memory_summary = self.memory.summarise_so_far()
        prior_ref = self.memory.prior_answer_on_topic(self.memory.current_topic) or ""

        prompt = f"""You are a document-aware support assistant. Answer the user's question strictly using only the provided SOURCE sections below. You must cite each SOURCE you use inline like [Doc Title §1.2 Section Name].

Prior conversation summary: {memory_summary}
{prior_ref}

If the answer was already provided earlier, say so briefly and reference the earlier point rather than repeating verbatim. If the user is switching topics, make that transition natural.

Answer clearly in 3-5 sentences. At the end, list the key points you covered as bullet points.

USER QUESTION:
{query}

SOURCE SECTIONS:
{context}

RESPONSE:"""
        content = self._call_llm(prompt)
        key_points = self._extract_points_from_text(content)
        return content, key_points, used_chunks

    def _call_llm(self, prompt: str) -> str:
        if ANTHROPIC_KEY:
            try:
                import anthropic  # type: ignore

                client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
                msg = client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=900,
                    messages=[{"role": "user", "content": prompt}],
                )
                parts = [getattr(b, "text", "") for b in getattr(msg, "content", []) if getattr(b, "type", "") == "text"]
                return "\n".join(parts).strip()
            except Exception as exc:
                return f"[LLM error: {exc}]"
        if OPENAI_KEY:
            try:
                from groq import Groq  # type: ignore
                from openai import OpenAI
                client = Groq(api_key=OPENAI_KEY)
                resp = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=900,
                temperature=0.2,
            )
                return (resp.choices[0].message.content or "").strip()
            except Exception as exc:
                return f"[LLM error: {exc}]"
        return ""

    def _extract_points_from_text(self, text: str) -> List[str]:
        points: List[str] = []
        for line in text.splitlines():
            s = line.strip()
            if s.startswith("- ") or s.startswith("* ") or (len(s) > 1 and s[0].isdigit() and s[1] in ".):"):
                points.append(s.lstrip("-*0123456789. :) ").strip())
        if not points:
            for sent in text.split(". "):
                candidate = sent.strip()
                if 20 < len(candidate) < 160:
                    points.append(candidate[:140])
                    if len(points) >= 3:
                        break
        return points[:5]

    def ask(self, user_query: str) -> AssistantResponse:
        topic_switch, old_topic, new_topic = self.memory.is_topic_switch(user_query)
        hints = self.memory.get_context_hints()
        avoid = self.memory.get_avoid_sections()

        hits = self.retriever.retrieve(user_query, top_k=6, context_hints=hints, avoid_sections=avoid)

        if topic_switch:
            clean_hints: List[str] = []
            if new_topic:
                clean_hints.extend(sorted(TOPIC_KEYWORDS.get(new_topic, set()))[:8])
            clean_hits = self.retriever.retrieve(user_query, top_k=6, context_hints=clean_hints, avoid_sections=[])
            scored_clean = {(c.doc_path, c.section_number): r for r in clean_hits for c in [r.chunk]}
            merged: list = []
            seen_keys: set = set()
            for r in clean_hits + hits:
                key = (r.chunk.doc_path, r.chunk.section_number)
                if key in seen_keys:
                    continue
                seen_keys.add(key)
                bonus = 0.0
                if key in scored_clean:
                    bonus = scored_clean[key].score * 0.8
                merged.append((r.score + bonus, r))
            merged.sort(key=lambda x: x[0], reverse=True)
            hits = [m[1] for m in merged[:6]]

        used_demo_fallback = False
        if USE_REAL_LLM:
            text, key_points, used_chunks = self._synthesize_real_llm(user_query, hits)
            if "[LLM error" in text or not used_chunks:
                text, key_points, used_chunks = self._synthesize_demo(user_query, hits)
                used_demo_fallback = True
        else:
            text, key_points, used_chunks = self._synthesize_demo(user_query, hits)

        prior_answer = self.memory.prior_answer_on_topic(new_topic or old_topic) if not topic_switch else None
        avoided = False
        note = None

        if used_demo_fallback:
            note = "Using built-in synthesis (LLM key configured but unavailable)"

        if topic_switch and old_topic and new_topic:
            switch_note = f"(Switching topic from '{old_topic}' to '{new_topic}'.) "
            text = switch_note + text
            switch_note_str = f"Topic switch detected: {old_topic} -> {new_topic}"
            note = (note + "; " + switch_note_str) if note else switch_note_str

        repeated = self.memory.find_repeated_fragment(text) if used_chunks else None
        if repeated and prior_answer:
            text = prior_answer + " " + text
            avoided = True
            avoid_note = "Avoided repeating previously-given info."
            note = (note + "; " + avoid_note) if note else avoid_note

        turn = self.memory.record_turn(user_query, text, used_chunks, key_points)

        return AssistantResponse(
            text=text,
            citations=used_chunks,
            key_points=key_points,
            topic=turn.topic,
            is_topic_switch=topic_switch,
            avoided_repetition=avoided,
            note=note,
        )
