from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
import pandas as pd
from db_handler import ReplitPgHandler

app = FastAPI(title="DIY Feedly Engine API")
db = ReplitPgHandler()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class NewFeedRequest(BaseModel):
    source_name: str
    rss_url: HttpUrl


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
        raise HTTPException(status_code=500, detail="Failed to read articles from database.")

    if df.empty:
        return []

    if "published_at" in df.columns:
        df["published_at"] = df["published_at"].astype(str)

    return df.to_dict(orient="records")


@app.post("/api/feeds")
def add_new_feed(feed_data: NewFeedRequest):
    """
    Accepts a new feed source, validates it, and inserts it into the database.
    """
    record = {"source_name": feed_data.source_name, "rss_url": str(feed_data.rss_url)}
    df_new_feed = pd.DataFrame([record])

    try:
        db.write_df_to_psql("rss_sources", df_new_feed, if_exists="append")
        return {
            "status": "success",
            "message": f"Successfully registered {feed_data.source_name}",
        }
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Failed to insert feed. The URL might already be registered.",
        )


@app.get("/api/health")
def health_status_check():
    """Confirms the web server is online and responsive."""
    return {"status": "online", "engine": "FastAPI Full-Stack System Active"}
