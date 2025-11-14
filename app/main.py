"""FastAPI application entry point"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.v1 import zones, companies, crawl, enrichment, outreach
from app.jobs.scheduled_jobs import start_scheduler
import atexit

app = FastAPI(
    title="TowPilot Lead Scraper API",
    description="Backend API for scraping and enriching towing company leads",
    version="0.1.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(zones.router, prefix="/api/v1/zones", tags=["zones"])
app.include_router(companies.router, prefix="/api/v1/companies", tags=["companies"])
app.include_router(crawl.router, prefix="/api/v1/crawl", tags=["crawl"])
app.include_router(enrichment.router, prefix="/api/v1/enrichment", tags=["enrichment"])
app.include_router(outreach.router, prefix="/api/v1/outreach", tags=["outreach"])

# Start scheduler on app startup
@app.on_event("startup")
async def startup_event():
    start_scheduler()

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

