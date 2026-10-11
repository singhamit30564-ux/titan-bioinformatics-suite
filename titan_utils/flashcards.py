"""Flashcards + a simplified ("lite") SM-2 spaced-repetition scheduler.

SM-2-lite
---------
This implements the core SuperMemo-2 idea — ease factor + growing interval,
reset to 1 day on a failed recall — without SM-2's original "repetition
number" edge cases for cards you have not reviewed in a long time. That
simplification is intentional for a classroom flashcard deck: it stays easy
to reason about and to unit test.

* ``quality`` is graded 0-5 (0 = total blank, 5 = perfect, easy recall).
* ``quality < 3`` resets the interval to 1 day (and gently lowers ease).
* ``quality >= 3`` grows the interval: 1 day -> 6 days -> ``interval * ease``.
* ``ease`` is clamped to a minimum of 1.3, matching the original algorithm.

Persistence: the browser-local review state (interval/ease/due_date/reviews
per card) round-trips through :mod:`titan_utils.local_storage`, which is a
small custom Streamlit component writing to ``window.localStorage`` — chosen
over ``st.query_params`` because query-param persistence would leak review
history into a shareable URL and has tight size limits. See that module's
docstring for the full rationale.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

__all__ = [
    "DATA_PATH",
    "CardState",
    "load_seed_cards",
    "new_card_state",
    "sm2_update",
    "is_due",
    "due_cards",
    "progress_counts",
    "merge_cards",
    "validate_custom_card",
    "FLIP_CARD_CSS",
    "flip_card_html",
]

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "flashcards.json"

DEFAULT_EASE = 2.5
MIN_EASE = 1.3


@dataclass
class CardState:
    """SM-2-lite scheduling state for one flashcard."""

    card_id: str
    interval: int = 0
    ease: float = DEFAULT_EASE
    due_date: str = ""  # ISO date, "" means "new / never reviewed -> due now"
    reviews: int = 0

    def as_dict(self) -> Dict[str, Any]:
        return {
            "card_id": self.card_id,
            "interval": self.interval,
            "ease": self.ease,
            "due_date": self.due_date,
            "reviews": self.reviews,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CardState":
        return cls(
            card_id=str(data.get("card_id", "")),
            interval=int(data.get("interval", 0) or 0),
            ease=float(data.get("ease", DEFAULT_EASE) or DEFAULT_EASE),
            due_date=str(data.get("due_date", "") or ""),
            reviews=int(data.get("reviews", 0) or 0),
        )


def load_seed_cards(path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Load the bundled Class-10/12 biology flashcard deck."""
    target = path or DATA_PATH
    with open(target, "r", encoding="utf-8") as handle:
        cards = json.load(handle)
    if not isinstance(cards, list):
        raise ValueError("flashcards.json must contain a JSON array of cards.")
    return cards


def new_card_state(card_id: str) -> CardState:
    """A never-reviewed card is due immediately."""
    return CardState(card_id=card_id, interval=0, ease=DEFAULT_EASE, due_date="", reviews=0)


def sm2_update(state: CardState, quality: int, today: Optional[date] = None) -> CardState:
    """Return the next :class:`CardState` after grading one review.

    ``quality`` is clamped to 0-5. ``today`` defaults to the real date and is
    only a parameter so tests can be deterministic.
    """
    quality = max(0, min(5, int(quality)))
    today = today or date.today()

    ease = state.ease + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    ease = max(MIN_EASE, round(ease, 3))

    if quality < 3:
        interval = 1
        reviews = 0  # a lapse restarts the "learning" ladder, SM-2 style
    else:
        reviews = state.reviews + 1
        if reviews == 1:
            interval = 1
        elif reviews == 2:
            interval = 6
        else:
            interval = max(1, round(state.interval * ease))

    due = today + timedelta(days=interval)
    return CardState(
        card_id=state.card_id,
        interval=interval,
        ease=ease,
        due_date=due.isoformat(),
        reviews=reviews,
    )


def is_due(state: CardState, today: Optional[date] = None) -> bool:
    """New cards (no due_date yet) and cards due today/earlier count as due."""
    if not state.due_date:
        return True
    today = today or date.today()
    try:
        due = datetime.strptime(state.due_date, "%Y-%m-%d").date()
    except ValueError:
        return True
    return due <= today


def due_cards(
    cards: List[Dict[str, Any]],
    states: Dict[str, CardState],
    today: Optional[date] = None,
) -> List[Dict[str, Any]]:
    """Filter ``cards`` down to the ones due for review today."""
    out = []
    for card in cards:
        state = states.get(card["id"], new_card_state(card["id"]))
        if is_due(state, today):
            out.append(card)
    return out


def progress_counts(
    cards: List[Dict[str, Any]],
    states: Dict[str, CardState],
    today: Optional[date] = None,
) -> Dict[str, int]:
    """Summary counts used by the Plotly progress chart."""
    today = today or date.today()
    total = len(cards)
    due = len(due_cards(cards, states, today))
    reviewed = sum(1 for c in cards if states.get(c["id"], new_card_state(c["id"])).reviews > 0)
    mastered = sum(
        1 for c in cards
        if states.get(c["id"], new_card_state(c["id"])).reviews >= 3
        and states.get(c["id"], new_card_state(c["id"])).interval >= 14
    )
    return {
        "total": total,
        "due": due,
        "reviewed": reviewed,
        "mastered": mastered,
        "new": total - reviewed,
    }


def merge_cards(seed_cards: List[Dict[str, Any]], custom_cards: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Combine the bundled deck with session/localStorage custom cards."""
    seen = {c["id"] for c in seed_cards}
    merged = list(seed_cards)
    for card in custom_cards:
        if card.get("id") not in seen:
            merged.append(card)
            seen.add(card.get("id"))
    return merged


FLIP_CARD_CSS = """
<style>
  .titan-fc-wrap { perspective: 1200px; margin: 6px 0 2px 0; }
  .titan-fc-checkbox { display: none; }
  .titan-fc-card {
    display: block; width: 100%; min-height: 170px; cursor: pointer;
    transform-style: preserve-3d; transition: transform 0.6s ease;
    position: relative;
  }
  .titan-fc-checkbox:checked + .titan-fc-card { transform: rotateY(180deg); }
  .titan-fc-face {
    position: absolute; inset: 0; backface-visibility: hidden;
    border-radius: 14px; border: 1px solid #2a3142; padding: 18px;
    display: flex; flex-direction: column; justify-content: center;
    background: #1a1f2e; box-sizing: border-box;
  }
  .titan-fc-front { color: #d4af37; font-size: 1.35rem; font-weight: 700; text-align: center; }
  .titan-fc-back {
    background: #11151f; color: #e0e0e0; font-size: 1.0rem; line-height: 1.5;
    transform: rotateY(180deg); text-align: center;
  }
  .titan-fc-chapter { color: #66fcf1; font-size: 0.72rem; letter-spacing: 0.04em;
    text-transform: uppercase; margin-top: 10px; text-align: center; }
  .titan-fc-hint { color: #8b9bb4; font-size: 0.72rem; text-align: center; margin-top: 6px; }
</style>
"""


def flip_card_html(card_id: str, term: str, definition: str, chapter: str) -> str:
    """Pure CSS 3D flip card (checkbox hack — no JavaScript required).

    The visual flip is independent of Streamlit's rerun cycle: clicking the
    card toggles a hidden ``<input type="checkbox">`` via its ``<label>``,
    which a CSS sibling selector uses to rotate the card. No ``st.session_state``
    round-trip is needed just to see the answer.
    """
    import html as _html

    safe_id = "".join(ch for ch in str(card_id) if ch.isalnum()) or "card"
    term_html = _html.escape(term)
    definition_html = _html.escape(definition)
    chapter_html = _html.escape(chapter)
    return f"""
<div class="titan-fc-wrap">
  <input type="checkbox" id="titan-fc-{safe_id}" class="titan-fc-checkbox">
  <label for="titan-fc-{safe_id}" class="titan-fc-card">
    <div class="titan-fc-face titan-fc-front">{term_html}</div>
    <div class="titan-fc-face titan-fc-back">{definition_html}</div>
  </label>
  <div class="titan-fc-chapter">{chapter_html}</div>
  <div class="titan-fc-hint">Tap the card to flip \u2194 front / back</div>
</div>
"""


def validate_custom_card(term: str, definition: str, chapter: str) -> Optional[str]:
    """Return an error message, or ``None`` when the custom card is valid."""
    if not term or not term.strip():
        return "Term cannot be empty."
    if not definition or not definition.strip():
        return "Definition cannot be empty."
    if len(term) > 120:
        return "Term is too long (120 characters max)."
    if len(definition) > 600:
        return "Definition is too long (600 characters max)."
    if not chapter or not chapter.strip():
        return "Please pick or enter a chapter tag."
    return None
