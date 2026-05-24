# DIY Feedly Aggregator Backend

A personal project prototyping a self-hosted RSS reader using Python, FastAPI, and PostgreSQL deployed on Replit.

## How to Run
1. Seed the database: `python seed_feeds.py`
2. Run the sync engine: `python sync_worker.py`
3. Launch the API: `uvicorn main:app --host 0.0.0.0 --port 8080`

## Routes

| Method     | URL           |
|------------|---------------|
| `POST`     | `/entities`   | 
| `GET`      | `/form`       | 
| `POST`     | `/form`       | 

## Testing


## Further Reading





