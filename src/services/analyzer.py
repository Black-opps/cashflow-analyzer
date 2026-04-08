"""
Real cashflow analysis service with proper calculations.
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from collections import defaultdict
import logging
import traceback

from ..core.database import SessionLocal, CashflowMetric, CashflowHourlyMetric

logger = logging.getLogger(__name__)


class CashflowAnalyzer:
    """Real cashflow analysis service."""
    
    def __init__(self):
        self.db = SessionLocal()
    
    def close(self):
        self.db.close()
    
    async def update_metrics(self, transaction: dict) -> None:
        """
        Update aggregated metrics for a single transaction.
        Called by Kafka consumer for each transaction.
        """
        tenant_id = transaction.get("tenant_id")
        amount = float(transaction.get("amount", 0))
        transaction_type = transaction.get("transaction_type", "expense")
        
        # Parse transaction date
        tx_date = datetime.fromisoformat(transaction.get("transaction_date", datetime.utcnow().isoformat()))
        period = tx_date.strftime("%Y-%m-%d")
        hour_rounded = tx_date.replace(minute=0, second=0, microsecond=0)
        
        try:
            # Update daily aggregate
            daily = self.db.query(CashflowMetric).filter(
                CashflowMetric.tenant_id == tenant_id,
                CashflowMetric.period == period
            ).first()
            
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
            hourly = self.db.query(CashflowHourlyMetric).filter(
                CashflowHourlyMetric.tenant_id == tenant_id,
                CashflowHourlyMetric.hour == hour_rounded
            ).first()
            
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
    
    async def get_summary(
        self, 
        tenant_id: str, 
        days: int = 30,
        group_by: str = "day"
    ) -> Dict:
        """
        Get cashflow summary with real calculations.
        """
        logger.info(f"=== get_summary called ===")
        logger.info(f"tenant_id: {tenant_id}, days: {days}, group_by: {group_by}")
        
        try:
            start_date = datetime.utcnow().date() - timedelta(days=days)
            start_date_str = start_date.isoformat()
            
            logger.info(f"Querying metrics for tenant {tenant_id} from {start_date_str}")
            
            # Query daily metrics
            metrics = self.db.query(CashflowMetric).filter(
                CashflowMetric.tenant_id == tenant_id,
                CashflowMetric.period >= start_date_str
            ).order_by(CashflowMetric.period).all()
            
            logger.info(f"Found {len(metrics)} metrics for tenant {tenant_id}")
            
            if not metrics:
                logger.info("No metrics found, returning empty summary")
                return self._empty_summary(days)
            
            # Calculate totals
            total_inflow = sum(m.inflow for m in metrics)
            total_outflow = sum(m.outflow for m in metrics)
            net_cashflow = total_inflow - total_outflow
            total_transactions = sum(m.transaction_count for m in metrics)
            
            logger.info(f"Totals - Inflow: {total_inflow}, Outflow: {total_outflow}, Net: {net_cashflow}")
            
            # Find largest
            largest_inflow = max((m.inflow for m in metrics), default=0)
            largest_outflow = max((m.outflow for m in metrics), default=0)
            
            # Calculate averages
            period_count = len(metrics)
            average_daily_inflow = total_inflow / period_count if period_count > 0 else 0
            average_daily_outflow = total_outflow / period_count if period_count > 0 else 0
            average_daily_net = net_cashflow / period_count if period_count > 0 else 0
            
            # Format details
            details = [
                {
                    "period": m.period,
                    "inflow": round(m.inflow, 2),
                    "outflow": round(m.outflow, 2),
                    "net": round(m.net, 2),
                    "transaction_count": m.transaction_count
                }
                for m in metrics
            ]
            
            result = {
                "summary": {
                    "total_inflow": round(total_inflow, 2),
                    "total_outflow": round(total_outflow, 2),
                    "net_cashflow": round(net_cashflow, 2),
                    "average_daily_inflow": round(average_daily_inflow, 2),
                    "average_daily_outflow": round(average_daily_outflow, 2),
                    "average_daily_net": round(average_daily_net, 2),
                    "largest_inflow": round(largest_inflow, 2),
                    "largest_outflow": round(largest_outflow, 2),
                    "transaction_count": total_transactions,
                    "period_count": period_count
                },
                "details": details,
                "group_by": group_by,
                "tenant_id": tenant_id,
                "period_start": start_date.isoformat(),
                "period_end": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Returning result with {len(details)} details")
            return result
            
        except Exception as e:
            logger.error(f"Error in get_summary: {e}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return self._empty_summary(days)
    
    async def get_real_time_stats(self, tenant_id: str, hours: int = 24) -> Dict:
        """
        Get real-time stats for the last N hours.
        """
        start_hour = datetime.utcnow().replace(minute=0, second=0, microsecond=0) - timedelta(hours=hours)
        
        hourly = self.db.query(CashflowHourlyMetric).filter(
            CashflowHourlyMetric.tenant_id == tenant_id,
            CashflowHourlyMetric.hour >= start_hour
        ).order_by(CashflowHourlyMetric.hour).all()
        
        total_inflow = sum(h.inflow for h in hourly)
        total_outflow = sum(h.outflow for h in hourly)
        
        return {
            "tenant_id": tenant_id,
            "hours": hours,
            "total_inflow": round(total_inflow, 2),
            "total_outflow": round(total_outflow, 2),
            "net": round(total_inflow - total_outflow, 2),
            "transaction_count": sum(h.transaction_count for h in hourly),
            "hourly_breakdown": [
                {
                    "hour": h.hour.isoformat(),
                    "inflow": round(h.inflow, 2),
                    "outflow": round(h.outflow, 2),
                    "net": round(h.net, 2),
                    "count": h.transaction_count
                }
                for h in hourly
            ]
        }
    
    async def detect_patterns(
        self,
        tenant_id: str,
        lookback_days: int = 90,
        min_confidence: float = 0.7
    ) -> List[Dict]:
        """
        Detect patterns in cashflow data using statistical analysis.
        """
        start_date = datetime.utcnow().date() - timedelta(days=lookback_days)
        
        metrics = self.db.query(CashflowMetric).filter(
            CashflowMetric.tenant_id == tenant_id,
            CashflowMetric.period >= start_date.isoformat()
        ).order_by(CashflowMetric.period).all()
        
        if len(metrics) < 14:
            return []
        
        patterns = []
        
        # Detect weekly seasonality
        weekly_pattern = self._detect_weekly_pattern(metrics)
        if weekly_pattern and weekly_pattern["confidence"] >= min_confidence:
            patterns.append({
                "pattern_type": "seasonal",
                "description": f"Weekly pattern detected: {weekly_pattern['description']}",
                "confidence": round(weekly_pattern["confidence"], 2),
                "affected_periods": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
                "suggested_action": "Schedule marketing campaigns on high-revenue days"
            })
        
        # Detect trends
        trend = self._detect_trend(metrics)
        if trend["confidence"] >= min_confidence:
            patterns.append({
                "pattern_type": "trend",
                "description": f"Cashflow is {trend['direction']} by approximately {trend['rate']:.0f}% over the last {lookback_days} days",
                "confidence": round(trend["confidence"], 2),
                "affected_periods": [m.period for m in metrics[-7:]],
                "suggested_action": trend["direction"] == "increasing" and "Continue current strategy" or "Review expenses and optimize operations"
            })
        
        # Detect anomalies
        anomalies = self._detect_anomalies(metrics)
        for anomaly in anomalies[:3]:
            if anomaly["confidence"] >= min_confidence:
                patterns.append({
                    "pattern_type": "anomaly",
                    "description": f"Unusual {anomaly['type']} of {anomaly['amount']:.0f} on {anomaly['date']}",
                    "confidence": round(anomaly["confidence"], 2),
                    "affected_periods": [anomaly["date"]],
                    "suggested_action": "Investigate unusual transaction pattern"
                })
        
        return patterns
    
    def _group_by_week(self, metrics: List[CashflowMetric]) -> List[Dict]:
        """Group daily metrics by week."""
        weeks = defaultdict(lambda: {"inflow": 0, "outflow": 0, "count": 0})
        
        for m in metrics:
            date = datetime.strptime(m.period, "%Y-%m-%d")
            week_key = f"{date.year}-W{date.isocalendar()[1]}"
            weeks[week_key]["inflow"] += m.inflow
            weeks[week_key]["outflow"] += m.outflow
            weeks[week_key]["count"] += m.transaction_count
        
        return [
            {
                "period": week,
                "inflow": round(data["inflow"], 2),
                "outflow": round(data["outflow"], 2),
                "net": round(data["inflow"] - data["outflow"], 2),
                "transaction_count": data["count"]
            }
            for week, data in sorted(weeks.items())
        ]
    
    def _group_by_month(self, metrics: List[CashflowMetric]) -> List[Dict]:
        """Group daily metrics by month."""
        months = defaultdict(lambda: {"inflow": 0, "outflow": 0, "count": 0})
        
        for m in metrics:
            month_key = m.period[:7]
            months[month_key]["inflow"] += m.inflow
            months[month_key]["outflow"] += m.outflow
            months[month_key]["count"] += m.transaction_count
        
        return [
            {
                "period": month,
                "inflow": round(data["inflow"], 2),
                "outflow": round(data["outflow"], 2),
                "net": round(data["inflow"] - data["outflow"], 2),
                "transaction_count": data["count"]
            }
            for month, data in sorted(months.items())
        ]
    
    def _to_metric_list(self, metrics: List[CashflowMetric]) -> List[Dict]:
        """Convert metrics to list of dicts."""
        return [
            {
                "period": m.period,
                "inflow": round(m.inflow, 2),
                "outflow": round(m.outflow, 2),
                "net": round(m.net, 2),
                "transaction_count": m.transaction_count
            }
            for m in metrics
        ]
    
    def _detect_weekly_pattern(self, metrics: List[CashflowMetric]) -> Optional[Dict]:
        """Detect weekly patterns using day-of-week analysis."""
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
            "confidence": confidence
        }
    
    def _detect_trend(self, metrics: List[CashflowMetric]) -> Dict:
        """Detect upward or downward trend."""
        if len(metrics) < 7:
            return {"direction": "stable", "rate": 0, "confidence": 0}
        
        recent = metrics[-7:]
        previous = metrics[-14:-7] if len(metrics) >= 14 else metrics[:7]
        
        recent_avg = sum(m.net for m in recent) / len(recent)
        previous_avg = sum(m.net for m in previous) / len(previous) if previous else recent_avg
        
        if recent_avg > previous_avg:
            direction = "increasing"
            rate = ((recent_avg - previous_avg) / (abs(previous_avg) + 1)) * 100
        else:
            direction = "decreasing"
            rate = ((previous_avg - recent_avg) / (abs(previous_avg) + 1)) * 100
        
        confidence = min(0.9, abs(recent_avg - previous_avg) / (abs(previous_avg) + 1000))
        
        return {"direction": direction, "rate": rate, "confidence": confidence}
    
    def _detect_anomalies(self, metrics: List[CashflowMetric]) -> List[Dict]:
        """Detect anomalous transactions using z-score."""
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
                    anomalies.append({
                        "date": m.period,
                        "type": "high_inflow" if m.net > 0 else "high_outflow",
                        "amount": abs(m.net),
                        "confidence": min(0.95, (z_score - 1) / 3)
                    })
        
        return sorted(anomalies, key=lambda x: x["confidence"], reverse=True)
    
    def _empty_summary(self, days: int) -> Dict:
        """Return empty summary when no data."""
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
                "period_count": 0
            },
            "details": [],
            "group_by": "day",
            "message": "No transactions found in the specified period"
        }