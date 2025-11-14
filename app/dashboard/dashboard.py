"""Main Textual dashboard application"""
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Static, DataTable, Label
from textual import events
from textual.reactive import reactive
from app.database import AsyncSessionLocal
from app.services.dashboard_service import DashboardService
from app.utils.time_periods import TimePeriod
import asyncio


class DashboardApp(App):
    """Main dashboard application"""
    
    CSS = """
    Screen {
        background: $surface;
    }
    
    .stats-card {
        height: 5;
        border: solid $primary;
        margin: 1;
        padding: 1;
    }
    
    .time-selector {
        dock: top;
        height: 3;
        background: $panel;
    }
    """
    
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("t", "set_period_today", "Today"),
        ("y", "set_period_yesterday", "Yesterday"),
        ("w", "set_period_this_week", "This Week"),
        ("l", "set_period_last_week", "Last Week"),
        ("m", "set_period_this_month", "This Month"),
        ("n", "set_period_last_month", "Last Month"),
        ("7", "set_period_7_days", "Last 7 Days"),
        ("1", "set_period_14_days", "Last 14 Days"),
        ("3", "set_period_30_days", "Last 30 Days"),
        ("r", "refresh", "Refresh"),
    ]
    
    current_period = reactive("today")
    
    def compose(self) -> ComposeResult:
        """Create child widgets"""
        yield Header(show_clock=True)
        yield Container(
            Label(f"Time Period: {self.current_period.upper()}", classes="time-selector"),
            Horizontal(
                Vertical(
                    Static("Companies", classes="stats-card"),
                    Static("Enrichment", classes="stats-card"),
                    Static("Outreach", classes="stats-card"),
                ),
                Vertical(
                    DataTable(id="companies-table"),
                    DataTable(id="zones-table"),
                ),
            ),
        )
        yield Footer()
    
    async on_mount(self) -> None:
        """Called when app starts"""
        await self.refresh_data()
        # Auto-refresh every 10 seconds
        self.set_interval(10.0, self.refresh_data)
    
    async def refresh_data(self) -> None:
        """Refresh dashboard data"""
        async with AsyncSessionLocal() as db:
            service = DashboardService()
            
            # Get overall stats
            stats = await service.get_dashboard_stats(db, self.current_period)
            
            # Update companies widget
            companies_widget = self.query_one("#companies-table", DataTable)
            companies_widget.clear()
            companies_widget.add_columns("Metric", "Value")
            companies_widget.add_row("Total Companies", str(stats['companies']['total']))
            companies_widget.add_row("New Companies", str(stats['companies']['new']))
            companies_widget.add_row("Websites Scraped", str(stats['enrichment']['websites_scraped']))
            companies_widget.add_row("Outreach Sent", str(stats['outreach']['sent']))
            companies_widget.add_row("Outreach Replied", str(stats['outreach']['replied']))
            companies_widget.add_row("Reply Rate", f"{stats['outreach']['reply_rate']:.1f}%")
            
            # Get zone stats
            zone_stats = await service.get_zone_stats(db, self.current_period)
            zones_widget = self.query_one("#zones-table", DataTable)
            zones_widget.clear()
            zones_widget.add_columns("Zone", "State", "Companies")
            for zone in zone_stats['zones']:
                zones_widget.add_row(
                    zone['name'],
                    zone['state'] or '',
                    str(zone['company_count'])
                )
    
    def action_set_period_today(self) -> None:
        """Set period to today"""
        self.current_period = TimePeriod.TODAY
        asyncio.create_task(self.refresh_data())
    
    def action_set_period_yesterday(self) -> None:
        """Set period to yesterday"""
        self.current_period = TimePeriod.YESTERDAY
        asyncio.create_task(self.refresh_data())
    
    def action_set_period_this_week(self) -> None:
        """Set period to this week"""
        self.current_period = TimePeriod.THIS_WEEK
        asyncio.create_task(self.refresh_data())
    
    def action_set_period_last_week(self) -> None:
        """Set period to last week"""
        self.current_period = TimePeriod.LAST_WEEK
        asyncio.create_task(self.refresh_data())
    
    def action_set_period_this_month(self) -> None:
        """Set period to this month"""
        self.current_period = TimePeriod.THIS_MONTH
        asyncio.create_task(self.refresh_data())
    
    def action_set_period_last_month(self) -> None:
        """Set period to last month"""
        self.current_period = TimePeriod.LAST_MONTH
        asyncio.create_task(self.refresh_data())
    
    def action_set_period_7_days(self) -> None:
        """Set period to last 7 days"""
        self.current_period = TimePeriod.LAST_7_DAYS
        asyncio.create_task(self.refresh_data())
    
    def action_set_period_14_days(self) -> None:
        """Set period to last 14 days"""
        self.current_period = TimePeriod.LAST_14_DAYS
        asyncio.create_task(self.refresh_data())
    
    def action_set_period_30_days(self) -> None:
        """Set period to last 30 days"""
        self.current_period = TimePeriod.LAST_30_DAYS
        asyncio.create_task(self.refresh_data())
    
    def action_refresh(self) -> None:
        """Refresh data"""
        asyncio.create_task(self.refresh_data())


def run_dashboard():
    """Run the dashboard"""
    app = DashboardApp()
    app.run()

