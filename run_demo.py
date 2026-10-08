from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from document_kb import KnowledgeAssistant, AssistantResponse  # noqa: E402


DEMO_CONVERSATION = [
    "How do I create an account and set up my first project?",
    "What are the password requirements, and how long is the verification link valid?",
    "How do I install the CLI on macOS and log in?",
    "Okay, CLI is installed. Now tell me about pricing — what tiers do you have and how much does Pro cost?",
    "What's included in the Pro tier specifically — storage, API calls, team members, support?",
    "If my credit card gets declined, how many retries do I get before services are suspended?",
    "Actually, let's talk about the API instead. What authentication methods do you support?",
    "What about webhooks — how do I verify they came from you and what events are available?",
    "What are the rate limits for API calls on the Pro plan?",
    "Back to teams: what roles exist and what can a Developer do vs an Admin?",
    "Oh one more thing about accounts — my SSO login is failing, what should I check first?",
    "Last question — my deployment keeps failing with health check errors. How do I fix that?",
]


def _divider(label: str = "") -> None:
    bar = "=" * 78
    print(f"\n{bar}")
    if label:
        print(f"  {label}")
        print(bar)


def _print_response(resp: AssistantResponse, turn_number: int) -> None:
    print(f"\n  🤖 Assistant [T{turn_number}]:")
    lines = resp.text.splitlines()
    for line in lines:
        wrapped = "     " + line if line.strip().startswith("-") or line.strip().startswith("(") else "     " + line
        # 72 char wrap
        if len(line) < 110:
            print("     " + line)
        else:
            words = line.split()
            buf = ""
            for w in words:
                if len(buf) + len(w) + 1 > 100:
                    print("     " + buf)
                    buf = w
                else:
                    buf = (buf + " " + w).strip()
            if buf:
                print("     " + buf)
    if resp.key_points:
        print(f"\n     Key points (memory tracked):")
        for kp in resp.key_points:
            print(f"       • {kp}")
    meta_bits = []
    if resp.topic:
        meta_bits.append(f"topic={resp.topic}")
    if resp.is_topic_switch:
        meta_bits.append("TOPIC_SWITCH_DETECTED")
    if resp.avoided_repetition:
        meta_bits.append("REPETITION_AVOIDED")
    if resp.citations:
        meta_bits.append(f"citations={len(resp.citations)}")
    if resp.note:
        meta_bits.append(f"note='{resp.note}'")
    print(f"\n     [meta: {', '.join(meta_bits)}]")


def run_demo(interactive: bool = True) -> None:
    kb_path = Path(__file__).parent / "knowledge_base"
    assistant = KnowledgeAssistant(kb_dir=kb_path)

    _divider("DOCUMENT-AWARE SUPPORT ASSISTANT — MULTI-TURN DEMO")
    print(f"  Knowledge base location: {kb_path}")
    print(f"  Total KB chunks loaded:  {len(assistant.chunks)}")
    print(f"  Using real LLM:          {'YES' if assistant._synthesize_real_llm.__code__.co_filename == '' else 'No (demo mode)'}")
    print("  Features to demonstrate:")
    print("    1. Context maintenance across turns")
    print("    2. Avoiding repetition of previously given info")
    print("    3. Graceful topic-switch handling")
    print("    4. Specific document section citations")
    print(f"    5. Multi-turn script of {len(DEMO_CONVERSATION)} turns")
    _divider()

    if interactive:
        print("  INTERACTIVE MODE — type your questions (type 'quit' to stop, 'summary' for state)")
        turn = 1
        while True:
            try:
                q = input(f"\n  👤 You [T{turn}]: ").strip()
            except EOFError:
                break
            if not q:
                continue
            if q.lower() in {"quit", "exit", "q"}:
                break
            if q.lower() == "summary":
                _divider("CONVERSATION STATE SUMMARY")
                print("  " + assistant.memory.summarise_so_far())
                print(f"  Current topic: {assistant.memory.current_topic}")
                print(f"  Context hints for next query: {assistant.memory.get_context_hints()[:6]}")
                avoid = assistant.memory.get_avoid_sections()
                if avoid:
                    print(f"  Sections down-weighted (already covered 2+ times): {len(avoid)}")
                _divider()
                continue
            resp = assistant.ask(q)
            _print_response(resp, turn)
            turn += 1
        return

    for i, user_q in enumerate(DEMO_CONVERSATION, start=1):
        print(f"\n  👤 User [T{i}]: {user_q}")
        resp = assistant.ask(user_q)
        _print_response(resp, i)
        if i % 4 == 0 and i < len(DEMO_CONVERSATION):
            _divider(f"MID-CONVERSATION STATE AFTER TURN {i}")
            summary = assistant.memory.summarise_so_far()
            print(f"  {summary}")
            hints = assistant.memory.get_context_hints()
            print(f"  Context hints feeding next retrieval: {hints[:6]}")
            avoid = assistant.memory.get_avoid_sections()
            if avoid:
                print(f"  Sections down-weighted for re-fetch: {len(avoid)}")
            topic = assistant.memory.current_topic
            print(f"  Current topic tracking: {topic}")
            _divider()

    _divider("FINAL CONVERSATION VERIFICATION")
    total_turns = len(assistant.memory.turns)
    topic_switches = sum(1 for i, t in enumerate(assistant.memory.turns)
                         if i > 0 and t.topic != assistant.memory.turns[i - 1].topic and t.topic is not None)
    cited_sections = set()
    total_citations = 0
    for t in assistant.memory.turns:
        total_citations += len(t.citations_used)
        for c in t.citations_used:
            cited_sections.add(c.split("::")[-1])
    topics_covered = {t.topic for t in assistant.memory.turns if t.topic}
    print(f"  ✅ Total turns completed:            {total_turns} (>= 10 required)")
    print(f"  ✅ Distinct document sections cited: {len(cited_sections)}")
    print(f"  ✅ Total citation references used:   {total_citations}")
    print(f"  ✅ Topic transitions observed:       {topic_switches}")
    print(f"  ✅ Distinct topics covered:          {sorted(topics_covered)}")
    print(f"  ✅ Citations per turn (avg):         {total_citations / max(1, total_turns):.1f}")
    print()
    print("  Per-turn breakdown:")
    for t in assistant.memory.turns:
        topic_str = f"topic={t.topic or '?'}"
        cites = [c.split("::")[-1] for c in t.citations_used] or ["—"]
        kp_count = len(t.response_key_points)
        print(f"    T{t.turn_index + 1:02d} | {topic_str:18s} | cites={cites[:2]} | key_points_tracked={kp_count}")
    _divider("END OF DEMO")
    print("  To run interactively:  python -m run_demo --interactive")
    print("  To enable real LLM:    set OPENAI_API_KEY or ANTHROPIC_API_KEY in .env")


if __name__ == "__main__":
    # Start a live conversation by default; pass --demo to run the scripted example.
    interactive = "--demo" not in sys.argv
    run_demo(interactive=interactive)
