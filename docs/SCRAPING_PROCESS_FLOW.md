# Scraping Process Flow

## Complete Pipeline Flow

```mermaid
flowchart TD
    Start([Zone Crawl Request]) --> ValidateZone{Zone Exists?}
    ValidateZone -->|No| Error1[Return 404 Error]
    ValidateZone -->|Yes| BuildLocation[Build Location String]
    
    BuildLocation --> ApifyCrawl[Apify Google Maps Crawl]
    ApifyCrawl --> ApifyWait{Wait for Completion}
    ApifyWait -->|Timeout| Error2[Return Partial Results]
    ApifyWait -->|Success| ProcessResults[Process Company Data]
    
    ProcessResults --> LoopStart{For Each Company}
    LoopStart --> CheckExists{Company Exists?<br/>by google_business_url}
    
    CheckExists -->|Yes| UpdateCompany[Update Existing Company]
    CheckExists -->|No| CreateCompany[Create New Company]
    
    UpdateCompany --> SetStage1[Set Stage: GOOGLE_MAPS]
    CreateCompany --> SetStage2[Set Stage: INITIAL]
    
    SetStage1 --> QueueCheck{Has Website?<br/>& scrape_websites=true}
    SetStage2 --> QueueCheck
    
    QueueCheck -->|Yes| AddToQueue[Add to Scraping Queue]
    QueueCheck -->|No| SkipScraping[Skip Website Scraping]
    
    AddToQueue --> NextCompany{More Companies?}
    SkipScraping --> NextCompany
    NextCompany -->|Yes| LoopStart
    NextCompany -->|No| BatchScrape[Batch Website Scraping]
    
    BatchScrape --> InitSemaphore[Initialize Semaphore<br/>Limit: 5 concurrent]
    InitSemaphore --> ScrapeLoop{For Each Company<br/>in Queue}
    
    ScrapeLoop --> AcquireLock[Acquire Semaphore Lock]
    AcquireLock --> ScrapeWebsite[Scrape Website<br/>Playwright Browser]
    
    ScrapeWebsite --> ExtractData{Extract Data}
    ExtractData --> ExtractHours[Extract Hours<br/>of Operation]
    ExtractData --> DetectImpound[Detect Impound<br/>Service]
    ExtractData --> ExtractServices[Extract Services]
    
    ExtractHours --> UpdateCompanyData[Update Company Record]
    DetectImpound --> UpdateCompanyData
    ExtractServices --> UpdateCompanyData
    
    UpdateCompanyData --> SetStage3[Set Stage: WEBSITE_SCRAPED]
    SetStage3 --> SetStatus[Set Status: success<br/>Update website_scraped_at]
    SetStatus --> ReleaseLock[Release Semaphore Lock]
    ReleaseLock --> ScrapeNext{More in Queue?}
    
    ScrapeWebsite -->|Error| HandleError[Handle Error]
    HandleError --> SetFailed[Set Status: failed<br/>Set Stage: FAILED]
    SetFailed --> ReleaseLock
    
    ScrapeNext -->|Yes| ScrapeLoop
    ScrapeNext -->|No| ProfileCheck{scrape_profiles=true?}
    
    ProfileCheck -->|Yes| ProfileScrape[Scrape Social Profiles]
    ProfileCheck -->|No| CalculateStats[Calculate Statistics]
    
    ProfileScrape --> Facebook{Has Facebook?}
    Facebook -->|Yes| ScrapeFB[Scrape Facebook Profile]
    Facebook -->|No| GoogleCheck{Has Google Business?}
    
    ScrapeFB --> GoogleCheck
    GoogleCheck -->|Yes| ScrapeGoogle[Scrape Google Business]
    GoogleCheck -->|No| UpdateStage[Update Stage if Complete]
    
    ScrapeGoogle --> UpdateStage
    UpdateStage --> SetFullyEnriched{All Sources<br/>Scraped?}
    SetFullyEnriched -->|Yes| SetStage4[Set Stage: FULLY_ENRICHED]
    SetFullyEnriched -->|No| CalculateStats
    
    SetStage4 --> CalculateStats
    
    CalculateStats --> BuildResponse[Build Response Object]
    BuildResponse --> Return[Return Statistics]
    
    style Start fill:#e1f5ff
    style Return fill:#d4edda
    style Error1 fill:#f8d7da
    style Error2 fill:#f8d7da
    style SetStage1 fill:#fff3cd
    style SetStage2 fill:#fff3cd
    style SetStage3 fill:#d1ecf1
    style SetStage4 fill:#d4edda
    style SetFailed fill:#f8d7da
```

## Stage Progression Flow

```mermaid
stateDiagram-v2
    [*] --> INITIAL: Company Discovered
    
    INITIAL --> GOOGLE_MAPS: Google Maps Data Collected
    
    GOOGLE_MAPS --> WEBSITE_SCRAPED: Website Scraped Successfully
    GOOGLE_MAPS --> FAILED: Website Scrape Failed
    
    WEBSITE_SCRAPED --> FACEBOOK_SCRAPED: Facebook Profile Scraped
    WEBSITE_SCRAPED --> FULLY_ENRICHED: No Social Profiles
    
    FACEBOOK_SCRAPED --> FULLY_ENRICHED: All Sources Complete
    
    FAILED --> WEBSITE_SCRAPED: Retry Successful
    FAILED --> FAILED: Retry Failed
    
    FULLY_ENRICHED --> WEBSITE_SCRAPED: Refresh Stale Data
    
    note right of INITIAL
        Just discovered
        No scraping done
    end note
    
    note right of GOOGLE_MAPS
        Apify data collected
        Basic info available
    end note
    
    note right of WEBSITE_SCRAPED
        Website scraped
        Hours, services extracted
    end note
    
    note right of FULLY_ENRICHED
        All sources scraped
        Complete data set
    end note
```

## Concurrent Website Scraping Flow

```mermaid
sequenceDiagram
    participant API as API Endpoint
    participant Orchestrator as ScrapingOrchestrator
    participant Semaphore as Semaphore (Limit: 5)
    participant Scraper as WebsiteScraperService
    participant DB as Database
    
    API->>Orchestrator: crawl_and_enrich_zone()
    Orchestrator->>Orchestrator: Discover Companies (Apify)
    Orchestrator->>DB: Store Companies
    
    Note over Orchestrator: Queue companies with websites
    
    loop For Each Company (Batch)
        Orchestrator->>Semaphore: acquire() - Wait if limit reached
        Semaphore-->>Orchestrator: Lock Acquired
        
        par Concurrent Scraping (Up to 5)
            Orchestrator->>Scraper: scrape_website(url)
            Scraper->>Scraper: Initialize Browser
            Scraper->>Scraper: Load Page
            Scraper->>Scraper: Extract Hours
            Scraper->>Scraper: Detect Impound
            Scraper->>Scraper: Extract Services
            Scraper-->>Orchestrator: Return Data
            
            Orchestrator->>DB: Update Company
            Orchestrator->>DB: Set Stage: WEBSITE_SCRAPED
            Orchestrator->>Semaphore: release()
        end
    end
    
    Orchestrator-->>API: Return Statistics
```

## Error Handling Flow

```mermaid
flowchart TD
    ScrapeAttempt[Attempt Website Scrape] --> TryScrape{Scrape Website}
    
    TryScrape -->|Success| ExtractSuccess[Extract Data Successfully]
    TryScrape -->|Network Error| RetryCheck1{Retry Count < 3?}
    TryScrape -->|Timeout| RetryCheck2{Retry Count < 3?}
    TryScrape -->|Parse Error| MarkFailed[Mark as Failed]
    
    RetryCheck1 -->|Yes| WaitRetry1[Wait 5 seconds]
    RetryCheck2 -->|Yes| WaitRetry2[Wait 5 seconds]
    RetryCheck1 -->|No| MarkFailed
    RetryCheck2 -->|No| MarkFailed
    
    WaitRetry1 --> TryScrape
    WaitRetry2 --> TryScrape
    
    ExtractSuccess --> ValidateData{Data Valid?}
    ValidateData -->|Yes| UpdateSuccess[Update Company<br/>Status: success]
    ValidateData -->|No| MarkPartial[Mark Partial Success<br/>Store Available Data]
    
    MarkFailed --> UpdateFailed[Update Company<br/>Status: failed<br/>Stage: FAILED]
    UpdateSuccess --> Continue[Continue to Next Company]
    MarkPartial --> Continue
    UpdateFailed --> Continue
    
    Continue --> QueueRetry{Add to Retry Queue?}
    QueueRetry -->|Yes| ScheduleRetry[Schedule Retry<br/>via refresh-stale endpoint]
    QueueRetry -->|No| End[End]
    ScheduleRetry --> End
```

## Status Tracking Flow

```mermaid
flowchart LR
    subgraph "Company Lifecycle"
        A[INITIAL<br/>Discovered] --> B[GOOGLE_MAPS<br/>Basic Data]
        B --> C[WEBSITE_SCRAPED<br/>Website Data]
        C --> D[FACEBOOK_SCRAPED<br/>Social Data]
        D --> E[FULLY_ENRICHED<br/>Complete]
        B --> F[FAILED<br/>Error]
        F --> C
    end
    
    subgraph "Status Fields"
        G[website_scrape_status<br/>pending/success/failed]
        H[website_scraped_at<br/>Timestamp]
        I[scraping_stage<br/>Current Stage]
    end
    
    A -.-> I
    B -.-> I
    C -.-> I
    D -.-> I
    E -.-> I
    F -.-> I
    
    C -.-> G
    C -.-> H
```

## Complete System Architecture

```mermaid
graph TB
    subgraph "API Layer"
        API1[POST /crawl/zone/{id}]
        API2[GET /crawl/status/{id}]
        API3[POST /crawl/refresh-stale]
    end
    
    subgraph "Service Layer"
        CrawlService[CrawlService]
        Orchestrator[ScrapingOrchestrator]
        ApifyService[ApifyService]
        EnrichmentService[EnrichmentService]
        WebsiteScraper[WebsiteScraperService]
    end
    
    subgraph "Data Sources"
        GoogleMaps[Google Maps<br/>via Apify]
        Websites[Company Websites<br/>via Playwright]
        Facebook[Facebook Profiles<br/>Future]
        GoogleBusiness[Google Business<br/>Future]
    end
    
    subgraph "Database"
        Companies[(Companies Table)]
        Snapshots[(Enrichment Snapshots)]
        Users[(Users Table)]
    end
    
    API1 --> CrawlService
    API2 --> Orchestrator
    API3 --> Orchestrator
    
    CrawlService --> Orchestrator
    Orchestrator --> ApifyService
    Orchestrator --> EnrichmentService
    Orchestrator --> WebsiteScraper
    
    ApifyService --> GoogleMaps
    WebsiteScraper --> Websites
    EnrichmentService --> Facebook
    EnrichmentService --> GoogleBusiness
    
    Orchestrator --> Companies
    EnrichmentService --> Snapshots
    Companies --> Snapshots
    
    style API1 fill:#e1f5ff
    style API2 fill:#e1f5ff
    style API3 fill:#e1f5ff
    style Orchestrator fill:#fff3cd
    style Companies fill:#d4edda
```

## Batch Processing Flow

```mermaid
flowchart TD
    StartBatch[Start Batch Processing] --> GetCompanies[Get Companies from Zone]
    GetCompanies --> FilterWebsites{Filter Companies<br/>with Websites}
    
    FilterWebsites -->|None| NoWebsites[Return: 0 websites]
    FilterWebsites -->|Found| CreateSemaphore[Create Semaphore<br/>Limit: 5]
    
    CreateSemaphore --> CreateTasks[Create Async Tasks<br/>for Each Company]
    CreateTasks --> GatherTasks[asyncio.gather<br/>All Tasks]
    
    GatherTasks --> Task1[Task 1: Scrape Company A]
    GatherTasks --> Task2[Task 2: Scrape Company B]
    GatherTasks --> Task3[Task 3: Scrape Company C]
    GatherTasks --> Task4[Task 4: Scrape Company D]
    GatherTasks --> Task5[Task 5: Scrape Company E]
    GatherTasks --> TaskN[Task N: ...]
    
    Task1 --> Acquire1[Acquire Lock]
    Task2 --> Acquire2[Acquire Lock]
    Task3 --> Acquire3[Acquire Lock]
    Task4 --> Acquire4[Acquire Lock]
    Task5 --> Acquire5[Acquire Lock]
    TaskN --> WaitQueue[Wait in Queue]
    
    Acquire1 --> Scrape1[Scrape Website]
    Acquire2 --> Scrape2[Scrape Website]
    Acquire3 --> Scrape3[Scrape Website]
    Acquire4 --> Scrape4[Scrape Website]
    Acquire5 --> Scrape5[Scrape Website]
    
    Scrape1 --> Release1[Release Lock]
    Scrape2 --> Release2[Release Lock]
    Scrape3 --> Release3[Release Lock]
    Scrape4 --> Release4[Release Lock]
    Scrape5 --> Release5[Release Lock]
    
    Release1 --> WaitQueue
    Release2 --> WaitQueue
    Release3 --> WaitQueue
    Release4 --> WaitQueue
    Release5 --> WaitQueue
    
    WaitQueue --> NextTask{Next Task Ready?}
    NextTask -->|Yes| AcquireNext[Acquire Lock]
    NextTask -->|No| CheckComplete{All Tasks<br/>Complete?}
    
    AcquireNext --> ScrapeNext[Scrape Website]
    ScrapeNext --> ReleaseNext[Release Lock]
    ReleaseNext --> CheckComplete
    
    CheckComplete -->|No| WaitQueue
    CheckComplete -->|Yes| AggregateResults[Aggregate Results]
    AggregateResults --> ReturnStats[Return Statistics]
    NoWebsites --> ReturnStats
    
    style StartBatch fill:#e1f5ff
    style ReturnStats fill:#d4edda
    style CreateSemaphore fill:#fff3cd
```

