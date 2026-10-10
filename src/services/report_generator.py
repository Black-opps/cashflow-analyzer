# cashflow-analyzer/src/services/report_generator.py - COMPLETE

from datetime import datetime
from typing import Any, Dict


class ReportGenerator:
    """Generate cashflow reports in various formats"""

    @staticmethod
    def generate_html_report(tenant_id: str, metrics: Dict[str, Any]) -> str:
        """Generate HTML report"""

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Cashflow Report - {tenant_id}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; color: #333; }}
                h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
                .metric {{ margin: 20px 0; padding: 15px; background: #f8f9fa; border-radius: 8px; }}
                .metric-label {{ font-weight: bold; color: #7f8c8d; }}
                .metric-value {{ font-size: 24px; font-weight: bold; color: #2c3e50; }}
                .positive {{ color: #27ae60; }}
                .negative {{ color: #e74c3c; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background-color: #3498db; color: white; }}
                .insight {{ margin: 10px 0; padding: 15px; border-left: 4px solid #3498db; background: #f8f9fa; }}
                .insight.positive {{ border-left-color: #27ae60; }}
                .insight.warning {{ border-left-color: #f39c12; }}
                .insight.critical {{ border-left-color: #e74c3c; }}
            </style>
        </head>
        <body>
            <h1>Cashflow Report</h1>
            <p><strong>Tenant:</strong> {tenant_id}</p>
            <p><strong>Generated:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
            
            <h2>Summary</h2>
            <div class="metric">
                <div class="metric-label">Total Income</div>
                <div class="metric-value positive">KES {metrics['total_income']:,.2f}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Total Expenses</div>
                <div class="metric-value negative">KES {metrics['total_expenses']:,.2f}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Net Cash Flow</div>
                <div class="metric-value {'positive' if metrics['net_cashflow'] >= 0 else 'negative'}">
                    KES {metrics['net_cashflow']:,.2f}
                </div>
            </div>
            <div class="metric">
                <div class="metric-label">Savings Rate</div>
                <div class="metric-value {'positive' if metrics['savings_rate'] >= 10 else 'negative'}">
                    {metrics['savings_rate']:.1f}%
                </div>
            </div>
            
            <h2>Top Expense Categories</h2>
            <table>
                <tr><th>Category</th><th>Amount</th><th>% of Total</th></tr>
        """

        for cat in metrics.get("top_expense_categories", []):
            pct = (
                (cat["amount"] / metrics["total_expenses"] * 100)
                if metrics["total_expenses"] > 0
                else 0
            )
            html += f"""
                <tr>
                    <td>{cat['category']}</td>
                    <td>KES {cat['amount']:,.2f}</td>
                    <td>{pct:.1f}%</td>
                </tr>
            """

        html += """
            </table>
            
            <h2>Insights</h2>
        """

        for insight in metrics.get("insights", []):
            insight_class = insight.get("type", "info")
            html += f"""
                <div class="insight {insight_class}">
                    <strong>{insight.get('title', '')}</strong>
                    <p>{insight.get('description', '')}</p>
                    <p><em>Action: {insight.get('action', 'N/A')}</em></p>
                    <small>Confidence: {insight.get('confidence', 0)*100:.0f}%</small>
                </div>
            """

        html += """
        </body>
        </html>
        """

        return html
