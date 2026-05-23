from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
import pandas as pd
from db_handler import ReplitPgHandler

app = FastAPI(title="DIY Feedly Engine API")
db = ReplitPgHandler()

# Allow open resource access configurations (CORS) for external frontend applications
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/articles")
def read_latest_articles():
    """
    Fetches and delivers the 50 most recent articles across all monitored
    feeds sorted chronologically by publication time stamp.
    """
    query = """
        SELECT a.id, a.title, a.link, a.summary, a.published_at, s.source_name 
        FROM articles a
        JOIN rss_sources s ON a.source_id = s.id
        ORDER BY a.published_at DESC NULLS LAST
        LIMIT 50;
    """
    df = db.read_sql_to_pd(query)

    if df is None:
        return {
            "error": "Failed to read data matrix components from remote database server."
        }

    if df.empty:
        return []

    # Safely transform complex datetime timestamp objects into standard text strings for JSON transfer
    if "published_at" in df.columns:
        df["published_at"] = df["published_at"].astype(str)

    return df.to_dict(orient="records")


@app.post("/api/feeds")
def add_new_feed(feed_data: NewFeedRequest):
    """
    Accepts a new feed from a web request, processes it into a DataFrame,
    and pushes it directly into the database.
    """
    # Extract validated string values from our Pydantic model
    record = {"source_name": feed_data.source_name, "rss_url": str(feed_data.rss_url)}

    # Wrap in a list and convert to a Pandas DataFrame
    df_new_feed = pd.DataFrame([record])

    try:
        # Write directly to our relational source table
        db.write_df_to_psql("rss_sources", df_new_feed, if_exists="append")
        return {
            "status": "success",
            "message": f"Successfully registered {feed_data.source_name}",
        }
    except Exception as e:
        # If the URL already exists, our database UNIQUE constraint blocks it and drops here
        raise HTTPException(
            status_code=400,
            detail="Failed to insert feed. The URL might already be registered.",
        )


@app.get("/api/health")
def health_status_check():
    """Confirms operational baseline responsiveness state for checking web server layer health."""
    return {"status": "online", "engine": "FastAPI Full-Stack System Active"}
