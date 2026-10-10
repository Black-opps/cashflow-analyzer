# cashflow-analyzer/src/services/analyzer.py - COMPLETE FINAL VERSION

"""
Real cashflow analysis service with proper calculations,
pattern detection, trend analysis, and anomaly detection.
"""

import logging
import traceback
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..core.database import (
    CashflowAnalysis,
    CashflowHourlyMetric,
    CashflowMetric,
    SessionLocal,
)
from ..core.logging import get_logger

logger = get_logger(__name__)


class CashflowAnalyzer:
    """Enhanced cashflow analysis service with pattern detection."""

    def __init__(self, db: Session = None):
        self.db = db or SessionLocal()
        self._closed = False

    def close(self):
        if not self._closed:
            self.db.close()
            self._closed = True

    async def update_metrics(self, transaction: dict) -> None:
        """Update aggregated metrics for a single transaction."""
        tenant_id = transaction.get("tenant_id")
        amount = float(transaction.get("amount", 0))
        transaction_type = transaction.get("transaction_type", "expense")

        tx_date = datetime.fromisoformat(
            transaction.get("transaction_date", datetime.utcnow().isoformat())
        )
        period = tx_date.strftime("%Y-%m-%d")
        hour_rounded = tx_date.replace(minute=0, second=0, microsecond=0)

        try:
            # Update daily aggregate
            daily = (
                self.db.query(CashflowMetric)
                .filter(
                    CashflowMetric.tenant_id == tenant_id,
                    CashflowMetric.period == period,
                )
                .first()
            )

            if not daily:
                daily = CashflowMetric(tenant_id=tenant_id, period=period)
                self.db.add(daily)

            if transaction_type == "income":
                daily.inflow += amount
            else:
                daily.outflow += amount

            daily.net = daily.inflow - daily.outflow
            daily.transaction_count += 1
            daily.updated_at = datetime.utcnow()

            # Update hourly aggregate
            hourly = (
                self.db.query(CashflowHourlyMetric)
                .filter(
                    CashflowHourlyMetric.tenant_id == tenant_id,
                    CashflowHourlyMetric.hour == hour_rounded,
                )
                .first()
            )

            if not hourly:
                hourly = CashflowHourlyMetric(tenant_id=tenant_id, hour=hour_rounded)
                self.db.add(hourly)

            if transaction_type == "income":
                hourly.inflow += amount
            else:
                hourly.outflow += amount

            hourly.net = hourly.inflow - hourly.outflow
            hourly.transaction_count += 1

            self.db.commit()
            logger.debug(f"Updated metrics for tenant {tenant_id}, period {period}")

        except Exception as e:
            logger.error(f"Failed to update metrics: {e}")
            self.db.rollback()
            raise

    async def analyze_batch(self, tenant_id: str, transactions: List[Dict]) -> Dict:
        """Analyze a batch of transactions."""
        logger.info(
            f"Analyzing {len(transactions)} transactions for tenant {tenant_id}"
        )

        metrics = self._calculate_metrics(transactions)
        metrics["tenant_id"] = tenant_id
        metrics["insights"] = self._generate_insights(metrics, len(transactions))
        metrics["patterns"] = await self.detect_patterns(tenant_id, lookback_days=30)

        self._store_analysis(tenant_id, metrics)
        return metrics

    def _calculate_metrics(self, transactions: List[Dict]) -> Dict[str, Any]:
        """Calculate comprehensive cashflow metrics."""
        metrics = {
            "total_income": 0.0,
            "total_expenses": 0.0,
            "net_cashflow": 0.0,
            "expense_by_category": {},
            "income_by_category": {},
            "daily_spending": {},
            "monthly_spending": {},
            "daily_income": {},
            "monthly_income": {},
            "average_transaction": 0.0,
            "largest_income": 0.0,
            "largest_expense": 0.0,
            "transaction_count": len(transactions),
            "expense_count": 0,
            "income_count": 0,
            "top_expense_categories": [],
            "top_income_categories": [],
            "savings_rate": 0.0,
            "expense_to_income_ratio": 0.0,
            "average_income": 0.0,
            "average_expense": 0.0,
        }

        total_amount_sum = 0.0
        expense_amounts = []
        income_amounts = []

        for txn in transactions:
            amount = float(txn.get("amount", 0))
            txn_type = txn.get("transaction_type", "").lower()
            category = txn.get("category", "Uncategorized")

            txn_date = txn.get("date", datetime.now().isoformat())
            try:
                if isinstance(txn_date, str):
                    if "T" in txn_date:
                        dt = datetime.fromisoformat(txn_date.replace("Z", "+00:00"))
                    else:
                        dt = datetime.strptime(txn_date, "%Y-%m-%d")
                else:
                    dt = txn_date
            except Exception:
                dt = datetime.now()

            day_key = dt.strftime("%Y-%m-%d")
            month_key = dt.strftime("%Y-%m")
            total_amount_sum += amount

            if txn_type in ["sent", "expense"]:
                metrics["total_expenses"] += amount
                metrics["expense_count"] += 1
                expense_amounts.append(amount)

                metrics["expense_by_category"][category] = (
                    metrics["expense_by_category"].get(category, 0) + amount
                )
                metrics["daily_spending"][day_key] = (
                    metrics["daily_spending"].get(day_key, 0) + amount
                )
                metrics["monthly_spending"][month_key] = (
                    metrics["monthly_spending"].get(month_key, 0) + amount
                )
                if amount > metrics["largest_expense"]:
                    metrics["largest_expense"] = amount
            else:
                metrics["total_income"] += amount
                metrics["income_count"] += 1
                income_amounts.append(amount)

                metrics["income_by_category"][category] = (
                    metrics["income_by_category"].get(category, 0) + amount
                )
                metrics["daily_income"][day_key] = (
                    metrics["daily_income"].get(day_key, 0) + amount
                )
                metrics["monthly_income"][month_key] = (
                    metrics["monthly_income"].get(month_key, 0) + amount
                )
                if amount > metrics["largest_income"]:
                    metrics["largest_income"] = amount

        metrics["net_cashflow"] = metrics["total_income"] - metrics["total_expenses"]

        if metrics["transaction_count"] > 0:
            metrics["average_transaction"] = (
                total_amount_sum / metrics["transaction_count"]
            )

        if metrics["income_count"] > 0:
            metrics["average_income"] = sum(income_amounts) / metrics["income_count"]

        if metrics["expense_count"] > 0:
            metrics["average_expense"] = sum(expense_amounts) / metrics["expense_count"]

        top_expense = sorted(
            metrics["expense_by_category"].items(), key=lambda x: x[1], reverse=True
        )[:5]
        metrics["top_expense_categories"] = [
            {"category": cat, "amount": amt} for cat, amt in top_expense
        ]

        top_income = sorted(
            metrics["income_by_category"].items(), key=lambda x: x[1], reverse=True
        )[:5]
        metrics["top_income_categories"] = [
            {"category": cat, "amount": amt} for cat, amt in top_income
        ]

        if metrics["total_income"] > 0:
            metrics["savings_rate"] = (
                metrics["net_cashflow"] / metrics["total_income"]
            ) * 100
            metrics["expense_to_income_ratio"] = (
                metrics["total_expenses"] / metrics["total_income"]
            ) * 100

        return metrics

    def _generate_insights(self, metrics: Dict, transaction_count: int) -> List[Dict]:
        """Generate insights from metrics."""
        insights = []

        if transaction_count < 10:
            insights.append(
                {
                    "type": "info",
                    "title": "More data needed",
                    "description": f"Only {transaction_count} transactions analyzed.",
                    "confidence": 0.5,
                }
            )
            return insights

        if metrics["net_cashflow"] > 0:
            insights.append(
                {
                    "type": "positive",
                    "title": "Positive Cash Flow",
                    "description": f"Surplus of KES {metrics['net_cashflow']:,.2f}.",
                    "confidence": 0.9,
                    "action": "Consider increasing savings or investments.",
                }
            )
        else:
            insights.append(
                {
                    "type": "warning",
                    "title": "Negative Cash Flow",
                    "description": f"Expenses exceed income by KES {abs(metrics['net_cashflow']):,.2f}.",
                    "confidence": 0.9,
                    "action": "Review top spending categories for potential savings.",
                }
            )

        if metrics["savings_rate"] > 20:
            insights.append(
                {
                    "type": "positive",
                    "title": f"Excellent Savings Rate: {metrics['savings_rate']:.1f}%",
                    "description": "Saving more than 20% of income.",
                    "confidence": 0.9,
                    "action": "Consider investing for long-term growth.",
                }
            )
        elif metrics["savings_rate"] > 10:
            insights.append(
                {
                    "type": "positive",
                    "title": f"Good Savings Rate: {metrics['savings_rate']:.1f}%",
                    "description": "Saving more than 10% of income.",
                    "confidence": 0.8,
                    "action": "Try to increase savings rate to 20%.",
                }
            )
        elif metrics["savings_rate"] < 0:
            insights.append(
                {
                    "type": "warning",
                    "title": "Negative Savings Rate",
                    "description": "Spending more than earning.",
                    "confidence": 0.9,
                    "action": "Review expenses and identify areas to reduce.",
                }
            )

        if metrics["top_expense_categories"]:
            top = metrics["top_expense_categories"][0]
            if top["amount"] > 0:
                insights.append(
                    {
                        "type": "insight",
                        "title": f"Top Expense: {top['category']}",
                        "description": f"KES {top['amount']:,.2f} spent on {top['category']}.",
                        "confidence": 0.85,
                        "action": f"Review {top['category']} spending for savings.",
                    }
                )

        if len(metrics["income_by_category"]) >= 3:
            insights.append(
                {
                    "type": "positive",
                    "title": "Diverse Income Sources",
                    "description": f"Income from {len(metrics['income_by_category'])} categories.",
                    "confidence": 0.85,
                    "action": "Maintain diverse income streams.",
                }
            )

        return insights

    def _store_analysis(self, tenant_id: str, metrics: Dict):
        """Store analysis results."""
        analysis = CashflowAnalysis(
            tenant_id=tenant_id,
            analysis_date=datetime.utcnow(),
            period_type="batch",
            period_start=datetime.utcnow() - timedelta(days=30),
            period_end=datetime.utcnow(),
            total_income=metrics["total_income"],
            total_expenses=metrics["total_expenses"],
            net_cashflow=metrics["net_cashflow"],
            savings_rate=metrics["savings_rate"],
            expense_to_income_ratio=metrics["expense_to_income_ratio"],
            transaction_count=metrics["transaction_count"],
            income_count=metrics["income_count"],
            expense_count=metrics["expense_count"],
            average_transaction=metrics["average_transaction"],
            average_income=metrics.get("average_income", 0),
            average_expense=metrics.get("average_expense", 0),
            largest_income=metrics["largest_income"],
            largest_expense=metrics["largest_expense"],
            expense_by_category=metrics["expense_by_category"],
            income_by_category=metrics["income_by_category"],
            top_expense_categories=metrics["top_expense_categories"],
            top_income_categories=metrics["top_income_categories"],
            daily_spending=metrics["daily_spending"],
            daily_income=metrics["daily_income"],
            insights=metrics.get("insights", []),
            analysis_version="1.0",
        )

        self.db.add(analysis)
        self.db.commit()
        logger.info(f"Stored cashflow analysis for tenant {tenant_id}")

    async def detect_patterns(
        self, tenant_id: str, lookback_days: int = 90, min_confidence: float = 0.7
    ) -> List[Dict]:
        """Detect patterns in cashflow data."""
        start_date = datetime.utcnow().date() - timedelta(days=lookback_days)

        metrics = (
            self.db.query(CashflowMetric)
            .filter(
                CashflowMetric.tenant_id == tenant_id,
                CashflowMetric.period >= start_date.isoformat(),
            )
            .order_by(CashflowMetric.period)
            .all()
        )

        if len(metrics) < 14:
            return []

        patterns = []

        # Weekly seasonality
        weekly_pattern = self._detect_weekly_pattern(metrics)
        if weekly_pattern and weekly_pattern["confidence"] >= min_confidence:
            patterns.append(
                {
                    "pattern_type": "seasonal",
                    "description": f"Weekly pattern: {weekly_pattern['description']}",
                    "confidence": round(weekly_pattern["confidence"], 2),
                    "affected_periods": [
                        "Monday",
                        "Tuesday",
                        "Wednesday",
                        "Thursday",
                        "Friday",
                        "Saturday",
                        "Sunday",
                    ],
                    "suggested_action": "Schedule campaigns on high-revenue days",
                }
            )

        # Trends
        trend = self._detect_trend(metrics)
        if trend["confidence"] >= min_confidence:
            patterns.append(
                {
                    "pattern_type": "trend",
                    "description": f"Cashflow is {trend['direction']} by {trend['rate']:.0f}% over {lookback_days} days",
                    "confidence": round(trend["confidence"], 2),
                    "affected_periods": [m.period for m in metrics[-7:]],
                    "suggested_action": (
                        "Continue current strategy"
                        if trend["direction"] == "increasing"
                        else "Review expenses"
                    ),
                }
            )

        # Anomalies
        anomalies = self._detect_anomalies(metrics)
        for anomaly in anomalies[:3]:
            if anomaly["confidence"] >= min_confidence:
                patterns.append(
                    {
                        "pattern_type": "anomaly",
                        "description": f"Unusual {anomaly['type']} of {anomaly['amount']:.0f} on {anomaly['date']}",
                        "confidence": round(anomaly["confidence"], 2),
                        "affected_periods": [anomaly["date"]],
                        "suggested_action": "Investigate unusual transaction pattern",
                    }
                )

        return patterns

    def _detect_weekly_pattern(self, metrics: List) -> Optional[Dict]:
        """Detect weekly patterns."""
        day_totals = defaultdict(float)
        day_counts = defaultdict(int)

        for m in metrics:
            date = datetime.strptime(m.period, "%Y-%m-%d")
            dow = date.strftime("%A")
            day_totals[dow] += m.net
            day_counts[dow] += 1

        if not day_totals:
            return None

        avg_per_day = {day: day_totals[day] / day_counts[day] for day in day_totals}
        max_day = max(avg_per_day, key=avg_per_day.get)
        min_day = min(avg_per_day, key=avg_per_day.get)

        variance = max(avg_per_day.values()) - min(avg_per_day.values())
        avg_all = sum(avg_per_day.values()) / len(avg_per_day)
        confidence = min(0.95, variance / (avg_all + 1))

        return {
            "description": f"Highest on {max_day} (avg {avg_per_day[max_day]:.0f}), lowest on {min_day} (avg {avg_per_day[min_day]:.0f})",
            "confidence": confidence,
        }

    def _detect_trend(self, metrics: List) -> Dict:
        """Detect trend direction."""
        if len(metrics) < 7:
            return {"direction": "stable", "rate": 0, "confidence": 0}

        recent = metrics[-7:]
        previous = metrics[-14:-7] if len(metrics) >= 14 else metrics[:7]

        recent_avg = sum(m.net for m in recent) / len(recent)
        previous_avg = (
            sum(m.net for m in previous) / len(previous) if previous else recent_avg
        )

        if recent_avg > previous_avg:
            direction = "increasing"
            rate = ((recent_avg - previous_avg) / (abs(previous_avg) + 1)) * 100
        else:
            direction = "decreasing"
            rate = ((previous_avg - recent_avg) / (abs(previous_avg) + 1)) * 100

        confidence = min(
            0.9, abs(recent_avg - previous_avg) / (abs(previous_avg) + 1000)
        )

        return {"direction": direction, "rate": rate, "confidence": confidence}

    def _detect_anomalies(self, metrics: List) -> List[Dict]:
        """Detect anomalies using z-score."""
        if len(metrics) < 7:
            return []

        net_values = [m.net for m in metrics]
        mean = sum(net_values) / len(net_values)
        std = (sum((x - mean) ** 2 for x in net_values) / len(net_values)) ** 0.5

        anomalies = []
        for m in metrics:
            if std > 0:
                z_score = abs(m.net - mean) / std
                if z_score > 2:
                    anomalies.append(
                        {
                            "date": m.period,
                            "type": "high_inflow" if m.net > 0 else "high_outflow",
                            "amount": abs(m.net),
                            "confidence": min(0.95, (z_score - 1) / 3),
                        }
                    )

        return sorted(anomalies, key=lambda x: x["confidence"], reverse=True)

    def _empty_summary(self, days: int) -> Dict:
        """Return empty summary."""
        return {
            "summary": {
                "total_inflow": 0,
                "total_outflow": 0,
                "net_cashflow": 0,
                "average_daily_inflow": 0,
                "average_daily_outflow": 0,
                "average_daily_net": 0,
                "largest_inflow": 0,
                "largest_outflow": 0,
                "transaction_count": 0,
                "period_count": 0,
            },
            "details": [],
            "group_by": "day",
            "message": "No transactions found",
        }


# ✅ Export both names for compatibility
CashflowAnalyzerService = CashflowAnalyzer
