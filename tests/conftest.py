"""Pytest configuration and shared fixtures"""
import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy import String, TypeDecorator
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from app.database import Base, get_db
from app.config import settings
from app.models import Zone, Company, EnrichmentSnapshot, OutreachHistory, OutreachSequence, OutreachAssignment
from uuid import uuid4


# GUID type for SQLite compatibility
class GUID(TypeDecorator):
    """Platform-independent GUID type for SQLite compatibility"""
    impl = String
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PostgresUUID())
        else:
            return dialect.type_descriptor(String(36))


# Test database URL (SQLite in-memory for testing)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False,
)

# Create test session factory
TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest.fixture(scope="function")
async def db_session():
    """Create a test database session with transaction rollback"""
    # Replace UUID columns with String for SQLite compatibility
    from sqlalchemy import String
    from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
    
    # Replace UUID with String in all tables for SQLite
    for table in Base.metadata.tables.values():
        for column in table.columns:
            if isinstance(column.type, PostgresUUID):
                column.type = String(36)
    
    # Create all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()
    
    # Drop all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def test_zone(db_session):
    """Create a test zone"""
    zone_id = uuid4()
    zone = Zone(
        id=str(zone_id),  # Convert to string for SQLite
        name="Test Zone",
        state="UT",
        zone_type="city",
        is_active=True
    )
    db_session.add(zone)
    await db_session.commit()
    await db_session.refresh(zone)
    return zone


@pytest.fixture
async def test_company(db_session, test_zone):
    """Create a test company"""
    company_id = uuid4()
    company = Company(
        id=str(company_id),  # Convert to string for SQLite
        name="Test Towing Company",
        zone_id=str(test_zone.id),  # Convert to string
        phone_primary="555-0100",
        google_business_url="https://maps.google.com/test",
        address_street="123 Main St",
        address_city="Salt Lake City",
        address_state="UT",
        address_zip="84101",
        source="test"
    )
    db_session.add(company)
    await db_session.commit()
    await db_session.refresh(company)
    return company


@pytest.fixture
def override_get_db(db_session):
    """Override get_db dependency for testing"""
    async def _get_db():
        yield db_session
    return _get_db


# Configure pytest-asyncio
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
