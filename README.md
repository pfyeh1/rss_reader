# DIY Feedly Aggregator Backend

A personal project prototyping a self-hosted RSS reader using Python, FastAPI, and PostgreSQL deployed on Replit.

## How to Run for the first time
1. Seed the database: `python seed_feeds.py`
2. Run the sync engine: `python sync_worker.py` - fetches article content given what rss urls are populated in the database
3. Launch the API: `uvicorn main:app --host 0.0.0.0 --port 8080`

## Subsequent Considerations
To fully deploy this app into production, sync_worker.py needs to be setup on a cron. Likely need to modify sync_worker.py to have more robust checking for new article content like implementing GUIDs (etags) and/or conditional headers (HTTP status 304).

## System Overview
```
  [ External RSS Feeds ] (NYTimes, BBC, etc.)
            │
            ▼ (Triggered via Scheduled Cron)
    ┌───────────────┐
    │ sync_worker.py│ ◄── [rss_sources Table] (Reads target URLs)
    └───────┬───────┘
            │
            ▼ (Filters Duplicates & Appends)
    ┌───────────────────────────────────┐
    │   REPLIT POSTGRESQL DATABASE      │
    │         [articles Table]          │
    └───────────────────────────────────┘
            ▲
            │ (Reads Prepared JSON Data on Request)
    ┌───────────────┐
    │    main.py    │ (FastAPI Web Server)
    └───────┬───────┘
            │
            ▼ (Serves HTTP Endpoints)
  [ Frontend User Client UI ] (Future State)
```

## Routes

| Method     | URL           |
|------------|---------------|
| `POST`     | `/feeds`   | 
| `GET`      | `/articles`       | 

## Testing
* Method 1: preview the app in Replit. Open new tab, copy the Url and type /docs to access the Swagger UI
* Open web browser and paste Replit app url and append /api/articles at the end.

## Further Reading





