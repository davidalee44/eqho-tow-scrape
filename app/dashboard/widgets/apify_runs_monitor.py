"""Apify Runs Monitor Widget"""
from textual.widgets import DataTable, Static
from textual.containers import Container, Vertical
from textual.reactive import reactive
from typing import Dict, Any, List, Optional
from datetime import datetime


class ApifyRunsMonitor(Container):
    """Widget for monitoring Apify runs in real-time"""
    
    runs_data: List[Dict[str, Any]] = []
    
    def compose(self):
        """Create widget layout"""
        with Vertical():
            yield Static("📊 Apify Runs Monitor", classes="widget-header")
            yield DataTable(id="apify-runs-table")
            yield Static("", id="apify-stats-summary")
    
    def on_mount(self):
        """Initialize widget"""
        table = self.query_one("#apify-runs-table", DataTable)
        table.add_columns(
            "Run ID",
            "Location",
            "Query",
            "Status",
            "Processing",
            "Items",
            "Started",
        )
        table.cursor_type = "row"
        self.update_stats_summary()
    
    def update_runs(self, runs: List[Dict[str, Any]]):
        """Update runs data"""
        self.runs_data = runs
        table = self.query_one("#apify-runs-table", DataTable)
        table.clear()
        
        for run in runs[:15]:  # Show last 15 runs
            status_emoji = {
                'RUNNING': '🟢',
                'SUCCEEDED': '✅',
                'FAILED': '❌',
                'ABORTED': '⏹️',
            }.get(run.get('status', ''), '⚪')
            
            processing_emoji = {
                'pending': '⏳',
                'processing': '🔄',
                'completed': '✅',
                'failed': '❌',
            }.get(run.get('processing_status', ''), '⚪')
            
            started = run.get('started_at', '')
            if started:
                try:
                    dt = datetime.fromisoformat(started.replace('Z', '+00:00'))
                    started = dt.strftime('%m/%d %H:%M')
                except:
                    pass
            
            table.add_row(
                run.get('run_id', 'N/A'),
                run.get('location', 'N/A')[:15],
                run.get('query', 'N/A')[:20],
                f"{status_emoji} {run.get('status', 'UNKNOWN')}",
                f"{processing_emoji} {run.get('processing_status', 'pending')}",
                str(run.get('items_count', 0)),
                started or 'N/A',
            )
        
        self.update_stats_summary()
    
    def update_stats_summary(self):
        """Update summary statistics"""
        summary = self.query_one("#apify-stats-summary", Static)
        
        if not self.runs_data:
            summary.update("No runs data available")
            return
        
        # Calculate stats
        active = sum(1 for r in self.runs_data if r.get('status') == 'RUNNING')
        succeeded = sum(1 for r in self.runs_data if r.get('status') == 'SUCCEEDED')
        failed = sum(1 for r in self.runs_data if r.get('status') == 'FAILED')
        pending = sum(1 for r in self.runs_data if r.get('processing_status') == 'pending')
        total_items = sum(r.get('items_count', 0) for r in self.runs_data)
        
        summary.update(
            f"🟢 Active: {active} | ✅ Succeeded: {succeeded} | ❌ Failed: {failed} | "
            f"⏳ Pending: {pending} | 📦 Total Items: {total_items:,}"
        )

