import pandas as pd
from db_handler import ReplitPgHandler


def add_feeds_to_database(new_feeds_dict):
    """
    Takes a dictionary of new feeds, structures them into a DataFrame,
    and safely appends them into the 'rss_sources' database table.
    """
    # 1. Initialize your custom database engine utility
    db = ReplitPgHandler()

    # 2. Flatten the nested dictionary into a list of row dictionaries
    flat_records = [
        {"source_name": name, "rss_url": url}
        for name, urls in new_feeds_dict.items()
        for url in urls
    ]

    # 3. Convert the structured list into a Pandas DataFrame
    df_new_feeds = pd.DataFrame(flat_records)

    # 4. Write the records to the database
    print(f"Attempting to add {len(df_new_feeds)} new feed sources to the database...")
    try:
        # Verify no duplicate URLs exist in the database before insertion
        existing_urls_df = db.read_sql_to_pd("SELECT rss_url FROM rss_sources")
        df_new_feeds1 = df_new_feeds[
            ~df_new_feeds["rss_url"].isin(existing_urls_df["rss_url"])
        ]
        if not df_new_feeds1.empty:
            # Use if_exists='append' and truncate_table=False so we NEVER wipe existing data
            db.write_df_to_psql("rss_sources", df_new_feeds, if_exists="append")
            print("Successfully pushed new feeds into the database!")

        else:
            print(f"Found {len(df_new_feeds1)} new unique URLs to add.")

    except Exception as e:
        print(f"Database write operation failed: {e}")
        print(
            "Tip: Check if you tried to insert a duplicate URL that already exists in the database."
        )


if __name__ == "__main__":
    # --- ADJUSTABLE PARAMETERS ---
    # Define any new feeds you want to add here.
    # Existing feeds already in your database will be preserved.
    my_new_feeds = {
        "techcrunch": ["https://techcrunch.com/feed/"],
        "wired": ["https://www.wired.com/feed/rss"],
    }

    # Execute the ingestion function
    add_feeds_to_database(my_new_feeds)
