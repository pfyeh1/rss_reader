import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
import pandas as pd
from google import genai
from google.genai import types
from db_handler import ReplitPgHandler

# Replit AI Integrations — managed Gemini service (no personal API key required)
_gemini_client = genai.Client(
    api_key=os.environ.get("AI_INTEGRATIONS_GEMINI_API_KEY"),
    http_options={
        "api_version": "",
        "base_url": os.environ.get("AI_INTEGRATIONS_GEMINI_BASE_URL"),
    },
)

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


@app.get("/api/ai_summary")
def generate_ai_summary():
    """
    On-Demand Endpoint: Pulls latest database content, constructs a prompt context,
    and returns a structured, bulleted AI news brief from Gemini.
    """
    query = """
        SELECT a.title, a.link, a.summary, a.published_at, s.source_name
        FROM articles a
        JOIN rss_sources s ON a.source_id = s.id
        ORDER BY a.published_at DESC NULLS LAST
        LIMIT 20;
    """

    df = db.read_sql_to_pd(query)
    if df is None or df.empty:
        raise HTTPException(status_code=500, detail="No articles found.")

    content = ""
    for _, row in df.iterrows():
        content += f"Source: {row['source_name']}\nTitle: {row['title']}\nSnippet: {row['summary']}\n---\n"

    prompt = f"Analyze the following recent news items and provide a unified, structured executive briefing:\n\n{content}."

    system_instruction = (
        "You are an executive assistant. Your task is to summarize the latest news "
        "in a concise, bulleted format that a busy executive can consume in an email without scrolling."
    )

    try:
        response = _gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.3,
                max_output_tokens=8192,
            ),
        )
        return {"status": "success", "ai_summary": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI processing failed: {str(e)}")


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
