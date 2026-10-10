# cashflow-analyzer/src/services/metrics.py - FIXED

import time
from contextlib import contextmanager  # ✅ ADD THIS

from prometheus_client import Counter, Gauge, Histogram


class MetricsService:
    """Service metrics collection"""

    # Counters
    analyses_total = Counter(
        "cashflow_analyses_total", "Total analyses performed", ["tenant_id", "status"]
    )
    alerts_triggered = Counter(
        "cashflow_alerts_total", "Total alerts triggered", ["tenant_id", "alert_type"]
    )

    # Histograms
    analysis_duration = Histogram(
        "cashflow_analysis_duration_seconds", "Analysis duration", ["tenant_id"]
    )
    transaction_batch_size = Histogram(
        "cashflow_transaction_batch_size", "Transaction batch size", ["tenant_id"]
    )

    # Gauges
    current_analysis_count = Gauge(
        "cashflow_current_analysis_count", "Current analyses in progress"
    )
    latest_savings_rate = Gauge(
        "cashflow_latest_savings_rate", "Latest savings rate", ["tenant_id"]
    )

    @classmethod
    def track_analysis(cls, tenant_id: str, metrics: dict):
        """Track an analysis"""
        cls.analyses_total.labels(tenant_id=tenant_id, status="success").inc()
        cls.transaction_batch_size.labels(tenant_id=tenant_id).observe(
            metrics.get("transaction_count", 0)
        )
        cls.latest_savings_rate.labels(tenant_id=tenant_id).set(
            metrics.get("savings_rate", 0)
        )

    @classmethod
    def track_alert(cls, tenant_id: str, alert_type: str):
        """Track an alert"""
        cls.alerts_triggered.labels(tenant_id=tenant_id, alert_type=alert_type).inc()

    @classmethod
    @contextmanager
    def measure_analysis(cls, tenant_id: str):
        """Context manager for measuring analysis duration"""
        start = time.time()
        try:
            cls.current_analysis_count.inc()
            yield
        finally:
            cls.current_analysis_count.dec()
            duration = time.time() - start
            cls.analysis_duration.labels(tenant_id=tenant_id).observe(duration)

    @classmethod
    def get_metrics(cls):
        """Get all metrics"""
        from prometheus_client import generate_latest

        return generate_latest()
