"""Import Progress Widget"""
from textual.widgets import DataTable, Static
from textual.containers import Container, Vertical, Horizontal
from typing import Dict, Any


class ImportProgressWidget(Container):
    """Widget for tracking company import progress"""
    
    progress_data: Dict[str, Any] = {}
    
    def compose(self):
        """Create widget layout"""
        with Vertical():
            yield Static("📥 Import Progress", classes="widget-header")
            with Horizontal():
                yield DataTable(id="import-stats-table")
                yield DataTable(id="import-stage-table")
            yield Static("", id="import-summary")
    
    def on_mount(self):
        """Initialize widget"""
        stats_table = self.query_one("#import-stats-table", DataTable)
        stats_table.add_columns("Metric", "Value")
        
        stage_table = self.query_one("#import-stage-table", DataTable)
        stage_table.add_columns("Stage", "Count")
        
        self.update_summary()
    
    def update_progress(self, data: Dict[str, Any]):
        """Update progress data"""
        self.progress_data = data
        
        # Update stats table
        stats_table = self.query_one("#import-stats-table", DataTable)
        stats_table.clear()
        stats_table.add_row("Total Companies", f"{data.get('total_companies', 0):,}")
        stats_table.add_row("With Impound", f"{data.get('with_impound', 0):,}")
        stats_table.add_row("Websites Scraped", f"{data.get('websites_scraped', 0):,}")
        stats_table.add_row("Recent (24h)", f"{data.get('recent_imports_24h', 0):,}")
        
        # Update stage table
        stage_table = self.query_one("#import-stage-table", DataTable)
        stage_table.clear()
        by_stage = data.get('by_stage', {})
        for stage, count in sorted(by_stage.items(), key=lambda x: x[1], reverse=True):
            stage_table.add_row(stage or 'None', f"{count:,}")
        
        self.update_summary()
    
    def update_summary(self):
        """Update summary text"""
        summary = self.query_one("#import-summary", Static)
        data = self.progress_data
        
        if not data:
            summary.update("No import data available")
            return
        
        total = data.get('total_companies', 0)
        impound = data.get('with_impound', 0)
        impound_pct = (impound / total * 100) if total > 0 else 0
        
        summary.update(
            f"📊 Total: {total:,} companies | "
            f"🚗 Impound: {impound:,} ({impound_pct:.1f}%) | "
            f"🌐 Scraped: {data.get('websites_scraped', 0):,} | "
            f"🆕 Recent: {data.get('recent_imports_24h', 0):,} (24h)"
        )

