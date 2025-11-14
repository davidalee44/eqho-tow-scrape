"""FastAPI application entry point"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.v1 import zones, companies, crawl, enrichment, outreach, eqho, auth, users, config, oidc, apify
from app.jobs.scheduled_jobs import start_scheduler
import atexit

app = FastAPI(
    title="TowPilot Lead Scraper API",
    description="Backend API for scraping and enriching towing company leads",
    version="0.1.0",
)

# CORS middleware
# In production, replace ["*"] with specific allowed origins
allowed_origins = ["*"] if settings.environment == "development" else [
    settings.supabase_url,
    "http://localhost:3000",
    "http://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include routers
# Auth endpoints (public)
app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(oidc.router, prefix="/api/v1/oidc", tags=["openid-connect"])
app.include_router(oidc.router, prefix="/.well-known", tags=["openid-connect"])

# Protected endpoints
app.include_router(zones.router, prefix="/api/v1/zones", tags=["zones"])
app.include_router(companies.router, prefix="/api/v1/companies", tags=["companies"])
app.include_router(crawl.router, prefix="/api/v1/crawl", tags=["crawl"])
app.include_router(enrichment.router, prefix="/api/v1/enrichment", tags=["enrichment"])
app.include_router(outreach.router, prefix="/api/v1/outreach", tags=["outreach"])
app.include_router(eqho.router, prefix="/api/v1/eqho", tags=["eqho"])

# User management endpoints (protected)
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])

# Configuration endpoints (admin only)
app.include_router(config.router, prefix="/api/v1/config", tags=["configuration"])

# Apify endpoints (protected)
app.include_router(apify.router, prefix="/api/v1/apify", tags=["apify"])

# Start scheduler on app startup
@app.on_event("startup")
async def startup_event():
    start_scheduler()
    
    # Load environment variables from Supabase if enabled
    if settings.use_supabase_env_vars:
        await settings.load_env_from_supabase_async()

@app.on_event("shutdown")
async def shutdown_event():
    from app.jobs.scheduled_jobs import stop_scheduler
    stop_scheduler()


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "TowPilot Lead Scraper API", "version": "0.1.0"}


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}

