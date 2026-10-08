from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class DocumentChunk:
    text: str
    doc_title: str
    doc_path: str
    section_number: str
    section_title: str
    chunk_index: int
    total_chunks_in_section: int
    char_start: int
    char_end: int
    keywords: List[str] = field(default_factory=list)


SECTION_HEADING_RE = re.compile(r"^(#{1,6})\s+((\d+(?:\.\d+)*)\.?\s+)?(.+)$", re.MULTILINE)
KEYWORD_RE = re.compile(r"\b([A-Z][A-Za-z0-9_]{2,}|[A-Z_]{3,}|API|CLI|SSO|SLA|RBAC|HMAC|SAML|OAuth|IdP|AES|PCI|DSS|TTL|CSV|JSON|HTTP|HTTPS|URL|IP|GB|MB|TB)\b")


def _extract_keywords(text: str) -> List[str]:
    matches = KEYWORD_RE.findall(text)
    seen = set()
    result = []
    for m in matches:
        if isinstance(m, tuple):
            token = m[0]
        else:
            token = m
        if token not in seen:
            seen.add(token)
            result.append(token)
    return result[:15]


def load_markdown_document(file_path: Path) -> List[DocumentChunk]:
    raw_text = file_path.read_text(encoding="utf-8")
    doc_title = file_path.stem.replace("_", " ").title()

    heading_spans: List[tuple] = []
    for m in SECTION_HEADING_RE.finditer(raw_text):
        level = len(m.group(1))
        number = m.group(3) or ""
        title = m.group(4).strip()
        heading_spans.append((m.start(), m.end(), level, number, title))

    if not heading_spans:
        return [DocumentChunk(
            text=raw_text.strip(),
            doc_title=doc_title,
            doc_path=str(file_path),
            section_number="",
            section_title=doc_title,
            chunk_index=0,
            total_chunks_in_section=1,
            char_start=0,
            char_end=len(raw_text),
            keywords=_extract_keywords(raw_text),
        )]

    sections: List[tuple] = []
    for i, (start, end, level, number, title) in enumerate(heading_spans):
        if i < len(heading_spans) - 1:
            section_end = heading_spans[i + 1][0]
        else:
            section_end = len(raw_text)
        section_text = raw_text[end:section_end].strip()
        if number:
            full_number = number
        else:
            full_number = f"L{level}"
        sections.append((full_number, title, end, section_end, section_text))

    chunks: List[DocumentChunk] = []
    CHUNK_TARGET = 600
    CHUNK_OVERLAP = 100

    for sec_num, sec_title, sec_char_start, sec_char_end, sec_text in sections:
        if len(sec_text) <= CHUNK_TARGET + CHUNK_OVERLAP:
            text = sec_text
            chunks.append(DocumentChunk(
                text=text,
                doc_title=doc_title,
                doc_path=str(file_path),
                section_number=sec_num,
                section_title=sec_title,
                chunk_index=0,
                total_chunks_in_section=1,
                char_start=sec_char_start,
                char_end=sec_char_end,
                keywords=_extract_keywords(text),
            ))
            continue

        words = sec_text.split()
        section_chunks_text: List[str] = []
        buffer: List[str] = []
        buf_len = 0
        for w in words:
            buffer.append(w)
            buf_len += len(w) + 1
            if buf_len >= CHUNK_TARGET:
                section_chunks_text.append(" ".join(buffer))
                overlap_words = buffer[-max(1, CHUNK_OVERLAP // 6):]
                buffer = overlap_words
                buf_len = sum(len(x) + 1 for x in buffer)
        if buffer:
            last = " ".join(buffer)
            if section_chunks_text and len(last) < 200:
                section_chunks_text[-1] = section_chunks_text[-1] + " " + last
            else:
                section_chunks_text.append(last)

        total = len(section_chunks_text)
        for idx, ctext in enumerate(section_chunks_text):
            chunks.append(DocumentChunk(
                text=ctext,
                doc_title=doc_title,
                doc_path=str(file_path),
                section_number=sec_num,
                section_title=sec_title,
                chunk_index=idx,
                total_chunks_in_section=total,
                char_start=sec_char_start,
                char_end=sec_char_end,
                keywords=_extract_keywords(ctext),
            ))
    return chunks


def load_knowledge_base(kb_dir: str | Path) -> List[DocumentChunk]:
    kb_path = Path(kb_dir)
    all_chunks: List[DocumentChunk] = []
    for md_file in sorted(kb_path.glob("*.md")):
        all_chunks.extend(load_markdown_document(md_file))
    return all_chunks
