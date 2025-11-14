"""Dashboard package"""
# Import only when needed to avoid circular imports
__all__ = ["DashboardApp", "run_dashboard"]

def __getattr__(name):
    """Lazy import to avoid import issues"""
    if name == "DashboardApp":
        from app.dashboard.dashboard import DashboardApp
        return DashboardApp
    if name == "run_dashboard":
        from app.dashboard.dashboard import run_dashboard
        return run_dashboard
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
