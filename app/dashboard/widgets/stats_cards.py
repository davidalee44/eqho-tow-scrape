"""Statistics Cards Widget"""
from textual.widgets import Static
from textual.containers import Container, Horizontal, Vertical
from typing import Dict, Any


class StatsCards(Container):
    """Widget displaying key statistics as cards"""
    
    def compose(self):
        """Create widget layout"""
        with Vertical():
            yield Static("📈 Key Statistics", classes="widget-header")
            with Horizontal():
                yield Static("", id="companies-card", classes="stat-card")
                yield Static("", id="zones-card", classes="stat-card")
                yield Static("", id="apify-card", classes="stat-card")
                yield Static("", id="import-card", classes="stat-card")
    
    def update_stats(self, stats: Dict[str, Any]):
        """Update statistics cards"""
        companies_card = self.query_one("#companies-card", Static)
        zones_card = self.query_one("#zones-card", Static)
        apify_card = self.query_one("#apify-card", Static)
        import_card = self.query_one("#import-card", Static)
        
        # Companies stats
        companies_total = stats.get('companies', {}).get('total', 0)
        companies_new = stats.get('companies', {}).get('new', 0)
        companies_card.update(
            f"🏢 Companies\n"
            f"Total: {companies_total:,}\n"
            f"New: {companies_new:,}"
        )
        
        # Zones stats
        zones = stats.get('zones', {}).get('zones', [])
        zones_count = len(zones)
        zones_card.update(
            f"🌍 Zones\n"
            f"Active: {zones_count}\n"
            f"Companies: {sum(z.get('company_count', 0) for z in zones):,}"
        )
        
        # Apify stats
        apify = stats.get('apify', {})
        apify_active = apify.get('active_runs', 0)
        apify_pending = apify.get('pending_processing', 0)
        apify_card.update(
            f"🤖 Apify Runs\n"
            f"Active: {apify_active}\n"
            f"Pending: {apify_pending}"
        )
        
        # Import stats
        import_data = stats.get('import', {})
        import_total = import_data.get('total_companies', 0)
        import_recent = import_data.get('recent_imports_24h', 0)
        import_card.update(
            f"📥 Imports\n"
            f"Total: {import_total:,}\n"
            f"24h: {import_recent:,}"
        )

