import feedparser
import pandas as pd
from db_handler import ReplitPgHandler

def run_sync_cycle():
    db = ReplitPgHandler()
    
    print("Reading target RSS sources list from database...")
    sources_df = db.read_sql_to_pd("SELECT id, rss_url FROM rss_sources")
    
    if sources_df is None or sources_df.empty:
        print("Sync aborted: No records present inside 'rss_sources' table.")
        return

    all_scouted_articles = []

    # Parse every URL listed inside the database
    for _, row in sources_df.iterrows():
        source_id = int(row['id'])
        rss_url = row['rss_url']
        
        print(f"Connecting to source feed stream: {rss_url}")
        feed = feedparser.parse(rss_url)
        
        for entry in feed.entries:
            all_scouted_articles.append({
                'source_id': source_id,
                'title': entry.get('title', 'Untitled Article'),
                'link': entry.get('link'),
                'summary': entry.get('summary', ''),
                'published_at': entry.get('published')
            })
            
    if not all_scouted_articles:
        print("No articles extracted from network feeds.")
        return

    df_incoming = pd.DataFrame(all_scouted_articles)
    
    # Clean historical records tracking to drop exact duplicates before database interaction
    df_incoming = df_incoming.dropna(subset=['link']).drop_duplicates(subset=['link'])

    # Query existing articles already saved locally to verify uniqueness
    existing_links_df = db.read_sql_to_pd("SELECT link FROM articles")
    
    if existing_links_df is not None and not existing_links_df.empty:
        existing_links_set = set(existing_links_df['link'].tolist())
        # Filter incoming processing buffer down to entirely non-existent entries
        df_final_upload = df_incoming[~df_incoming['link'].isin(existing_links_set)]
    else:
        df_final_upload = df_incoming

    # Write unique elements
    if not df_final_upload.empty:
        # Standard datetime formatting patch block to ensure PostgreSQL timestamps validation
        df_final_upload['published_at'] = pd.to_datetime(df_final_upload['published_at'], errors='coerce')
        db.write_df_to_psql("articles", df_final_upload, if_exists='append')
        print(f"Cycle completed successfully. Logged {len(df_final_upload)} new unique articles.")
    else:
        print("Synchronization completed. Zero new articles found.")

if __name__ == "__main__":
    run_sync_cycle()
