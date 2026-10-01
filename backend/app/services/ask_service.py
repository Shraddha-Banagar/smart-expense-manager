"""
The expense Q&A assistant (POST /api/ai/ask). Unlike receipt extraction,
this genuinely needs a language model — questions are open-ended natural
language ("how can I reduce unnecessary spending?").

Safety design (see important_requirement / ai_safety in the spec: the
assistant must use the authenticated user's actual data and must not
invent financial information):

1. The ONLY expense data the model ever sees is a compact, explicitly
   built JSON summary (build_financial_context) — computed straight from
   this user's own rows via the same trusted analytics/budget services
   used elsewhere in the app. The model is never given raw database
   access or a way to query for more.
2. The prompt explicitly instructs the model to answer only from that
   context and to say so plainly if the context doesn't cover the
   question, rather than guessing at numbers.
3. Every answer carries a fixed disclaimer that this is informational,
   not financial advice (the endpoint appends this; it isn't left to the
   model to remember).

This does NOT make hallucination impossible — an LLM can still ignore
instructions. It bounds the blast radius: the model can misstate or
misinterpret the numbers it was given, but it has no channel to invent an
entirely fabricated transaction that isn't in the app's own data, and
nothing it says here is ever written back to the database.
"""
import logging
from datetime import date

from dateutil.relativedelta import relativedelta
from sqlalchemy.orm import Session

from app.services import ai_service
from app.services.analytics_service import get_summary, get_category_breakdown, get_monthly_trend
from app.services.budget_service import list_budgets

logger = logging.getLogger("expense_manager")

DISCLAIMER = "This is based on your logged expense data and is for informational purposes only — not financial advice."

MAX_HISTORY_TURNS = 6  # cap how much prior conversation we forward, for prompt size/cost


def build_financial_context(db: Session, user_id: int) -> dict:
    """
    The complete, and ONLY, set of facts about this user's finances that
    the assistant is allowed to reason from.
    """
    today = date.today()
    this_month_start = today.replace(day=1)
    last_month_end = this_month_start - relativedelta(days=1)
    last_month_start = last_month_end.replace(day=1)

    summary = get_summary(db, user_id)
    categories = get_category_breakdown(db, user_id)
    # Explicit this-month / last-month breakdowns so "this month" and
    # "which category increased" questions aren't answered from all-time
    # totals by mistake.
    this_month_categories = get_category_breakdown(db, user_id, date_from=this_month_start, date_to=today)
    last_month_categories = get_category_breakdown(db, user_id, date_from=last_month_start, date_to=last_month_end)
    monthly = get_monthly_trend(db, user_id, months=6)
    budgets = list_budgets(db, user_id)

    return {
        "today": today.isoformat(),
        "summary": summary.model_dump(),
        "spending_by_category_this_month": [c.model_dump() for c in this_month_categories],
        "spending_by_category_last_month": [c.model_dump() for c in last_month_categories],
        "spending_by_category_all_time": [c.model_dump() for c in categories],
        "monthly_trend_last_6_months": [m.model_dump() for m in monthly],
        "budgets": [
            {
                "category": b.category,
                "monthly_limit": b.monthly_limit,
                "spent_this_month": b.spent_amount,
                "percentage_used": b.percentage_used,
                "status": b.status,
            }
            for b in budgets
        ],
    }


def _build_prompt(question: str, context: dict, history: list[dict]) -> str:
    history_text = ""
    if history:
        turns = history[-MAX_HISTORY_TURNS:]
        history_text = "\n".join(f"{turn['role']}: {turn['content']}" for turn in turns)
        history_text = f"\nPrior conversation:\n{history_text}\n"

    return f"""You are a personal expense assistant. Answer the user's question using ONLY the financial data provided below — never guess, estimate, or invent numbers that aren't in this data.

If the data doesn't contain enough information to answer the question, say so plainly (e.g. "I don't have enough data to answer that yet") rather than making something up.

You are not a licensed financial advisor. Keep answers concise (a few sentences), factual, and grounded strictly in the data below.

User's financial data (JSON):
{context}
{history_text}
User's question: {question}

Answer:"""


def ask_question(db: Session, user_id: int, question: str, history: list[dict] | None = None) -> str:
    """
    Returns the assistant's answer. Raises AIConfigError if no provider is
    configured (the router turns that into a clear 503). Any other failure
    (network error, provider outage, etc.) degrades to a safe fallback
    message rather than a 500 — the same "never crash the request, always
    give the user something sensible" pattern as expense extraction.
    """
    context = build_financial_context(db, user_id)
    prompt = _build_prompt(question, context, history or [])

    try:
        return ai_service._call_llm(prompt).strip()
    except ai_service.AIConfigError:
        raise
    except Exception:
        logger.exception("LLM call failed during ask_question.")
        return (
            "Sorry, I couldn't process that question right now. "
            "Please try again in a moment."
        )
