"""
Spending insights: deliberately rule-based, NOT LLM-generated.

The spec's own example insights ("Your highest spending category this
month is Food") are exact statements of fact about the user's real data,
and the spec's ai_safety requirements are explicit: don't invent
transactions, don't invent financial information. Computing these facts
directly in Python from the database guarantees they're always accurate
and gives zero hallucination surface — there's nothing here an LLM could
get wrong, because there's no LLM in this path at all.

The AI-assisted piece of "AI Insights" is the natural-language Q&A
assistant (see ask_service.py / /api/ai/ask), where open-ended questions
genuinely need a language model. Insights don't.
"""
from datetime import date

from dateutil.relativedelta import relativedelta
from sqlalchemy.orm import Session

from app.schemas.insights import InsightItem, InsightsResponse
from app.services.analytics_service import get_summary, get_category_breakdown, _get_expenses
from app.services.budget_service import list_budgets

DISCLAIMER = (
    "These insights are generated from your logged expenses for informational "
    "purposes only. They are not financial advice."
)


def _this_and_last_month_expenses(db: Session, user_id: int):
    today = date.today()
    this_month_start = today.replace(day=1)
    last_month_end = this_month_start - relativedelta(days=1)
    last_month_start = last_month_end.replace(day=1)

    this_month = _get_expenses(db, user_id, date_from=this_month_start, date_to=today)
    last_month = _get_expenses(db, user_id, date_from=last_month_start, date_to=last_month_end)
    return this_month, last_month


def generate_insights(db: Session, user_id: int) -> InsightsResponse:
    insights: list[InsightItem] = []

    this_month_expenses, last_month_expenses = _this_and_last_month_expenses(db, user_id)

    if not this_month_expenses:
        insights.append(InsightItem(
            message="You haven't logged any expenses this month yet.",
            type="info",
        ))
    else:
        # 1. Highest spending category this month
        categories = get_category_breakdown(db, user_id, date_from=date.today().replace(day=1), date_to=date.today())
        if categories:
            top = categories[0]
            insights.append(InsightItem(
                message=f"Your highest spending category this month is {top.category} ({_fmt(top.total)}).",
                type="info",
            ))

        # 2. Month-over-month total spending change
        this_month_total = sum(e.amount for e in this_month_expenses)
        last_month_total = sum(e.amount for e in last_month_expenses)
        if last_month_total > 0:
            pct_change = ((this_month_total - last_month_total) / last_month_total) * 100
            if pct_change > 5:
                insights.append(InsightItem(
                    message=f"Your spending increased by {abs(round(pct_change))}% compared with last month.",
                    type="warning",
                ))
            elif pct_change < -5:
                insights.append(InsightItem(
                    message=f"Your spending decreased by {abs(round(pct_change))}% compared with last month.",
                    type="positive",
                ))

        # 3. Average transaction amount change
        this_month_avg = this_month_total / len(this_month_expenses) if this_month_expenses else 0
        last_month_avg = (sum(e.amount for e in last_month_expenses) / len(last_month_expenses)) if last_month_expenses else 0
        if last_month_avg > 0:
            avg_pct_change = ((this_month_avg - last_month_avg) / last_month_avg) * 100
            if avg_pct_change > 10:
                insights.append(InsightItem(
                    message="Your average transaction amount increased this month.",
                    type="warning",
                ))
            elif avg_pct_change < -10:
                insights.append(InsightItem(
                    message="Your average transaction amount decreased this month.",
                    type="positive",
                ))

    # 4. Budget warnings — always checked, independent of whether there are
    # expenses this month, since a 0%-used budget is itself useful context.
    for budget in list_budgets(db, user_id):
        if budget.status == "exceeded":
            insights.append(InsightItem(
                message=f"You spent more than your monthly budget on {budget.category} "
                        f"({_fmt(budget.spent_amount)} of {_fmt(budget.monthly_limit)}).",
                type="warning",
            ))
        elif budget.status == "approaching":
            insights.append(InsightItem(
                message=f"You're approaching your monthly budget for {budget.category} "
                        f"({budget.percentage_used}% used).",
                type="warning",
            ))

    if not insights:
        insights.append(InsightItem(
            message="Nothing notable to report yet — keep logging expenses to unlock more insights.",
            type="info",
        ))

    return InsightsResponse(insights=insights, disclaimer=DISCLAIMER)


def _fmt(amount: float) -> str:
    return f"₹{amount:,.2f}"
