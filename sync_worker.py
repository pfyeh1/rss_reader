import feedparser
import pandas as pd
from db_handler import ReplitPgHandler

_FETCH_TIMEOUT_SECONDS = 10


def run_sync_cycle():
    db = ReplitPgHandler()

    print("Reading target RSS sources list from database...")
    sources_df = db.read_sql_to_pd("SELECT id, rss_url FROM rss_sources")

    if sources_df is None or sources_df.empty:
        print("Sync aborted: No records present inside 'rss_sources' table.")
        return

    all_scouted_articles = []

    for _, row in sources_df.iterrows():
        source_id = int(row["id"])
        rss_url = row["rss_url"]

        print(f"Connecting to source feed stream: {rss_url}")
        try:
            feed = feedparser.parse(rss_url, request_headers={"Connection": "close"})
        except Exception as e:
            print(f"Failed to fetch feed {rss_url}: {e}")
            continue

        for entry in feed.entries:
            link = entry.get("link")
            if not link:
                continue
            all_scouted_articles.append({
                "source_id": source_id,
                "title": entry.get("title", "Untitled Article"),
                "link": link,
                "summary": entry.get("summary", ""),
                "published_at": entry.get("published"),
            })

    if not all_scouted_articles:
        print("No articles extracted from network feeds.")
        return

    df_incoming = pd.DataFrame(all_scouted_articles)
    df_incoming = df_incoming.drop_duplicates(subset=["link"])

    # Convert timestamps before upsert
    df_incoming["published_at"] = pd.to_datetime(df_incoming["published_at"], errors="coerce")

    # Use DB-level conflict handling to skip duplicates — avoids full table scan
    engine = db.generate_engine()
    inserted = 0
    skipped = 0
    try:
        with engine.connect() as conn:
            for _, article in df_incoming.iterrows():
                result = conn.execute(
                    sqlalchemy_text(
                        """
                        INSERT INTO articles (source_id, title, link, summary, published_at)
                        VALUES (:source_id, :title, :link, :summary, :published_at)
                        ON CONFLICT (link) DO NOTHING
                        """
                    ),
                    {
                        "source_id": article["source_id"],
                        "title": article["title"],
                        "link": article["link"],
                        "summary": article["summary"],
                        "published_at": article["published_at"] if pd.notna(article["published_at"]) else None,
                    },
                )
                if result.rowcount > 0:
                    inserted += 1
                else:
                    skipped += 1
            conn.commit()
    finally:
        engine.dispose()

    print(f"Cycle completed. Inserted {inserted} new articles, skipped {skipped} duplicates.")


# Import here to keep it at module level but avoid circular confusion
from sqlalchemy import text as sqlalchemy_text

if __name__ == "__main__":
    run_sync_cycle()
