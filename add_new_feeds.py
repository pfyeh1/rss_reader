import pandas as pd
from db_handler import ReplitPgHandler


def add_feeds_to_database(new_feeds_dict):
    """
    Takes a dictionary of new feeds, structures them into a DataFrame,
    and safely appends only new (non-duplicate) entries to the 'rss_sources' table.
    """
    db = ReplitPgHandler()

    flat_records = [
        {"source_name": name, "rss_url": url}
        for name, urls in new_feeds_dict.items()
        for url in urls
    ]

    df_new_feeds = pd.DataFrame(flat_records)
    print(f"Checking {len(df_new_feeds)} candidate feed sources against the database...")

    try:
        existing_urls_df = db.read_sql_to_pd("SELECT rss_url FROM rss_sources")

        if existing_urls_df is not None and not existing_urls_df.empty:
            df_to_insert = df_new_feeds[
                ~df_new_feeds["rss_url"].isin(existing_urls_df["rss_url"])
            ]
        else:
            df_to_insert = df_new_feeds

        if not df_to_insert.empty:
            db.write_df_to_psql("rss_sources", df_to_insert, if_exists="append")
            print(f"Successfully added {len(df_to_insert)} new feed source(s) to the database.")
        else:
            print("No new feeds to add — all provided URLs are already registered.")

    except Exception as e:
        print(f"Database write operation failed: {e}")
        print("Tip: Check if you tried to insert a duplicate URL that already exists in the database.")


if __name__ == "__main__":
    my_new_feeds = {
        "techcrunch": ["https://techcrunch.com/feed/"],
        "wired": ["https://www.wired.com/feed/rss"],
    }

    add_feeds_to_database(my_new_feeds)
