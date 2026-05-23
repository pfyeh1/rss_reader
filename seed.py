import pandas as pd
from db_handler import ReplitPgHandler


def seed_initial_feeds():
    """
    Seeds the internal Replit PostgreSQL database with initial RSS URLs.
    """
    # 1. Initialize our Replit database utility handler
    db = ReplitPgHandler()

    # 2. Define the target feed data using your dictionary layout
    feeds_dict = {
        "nytimes": [
            "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
            "https://rss.nytimes.com/services/xml/rss/nyt/AsiaPacific.xml",
        ],
        "bbc": [
            "http://feeds.bbci.co.uk/news/rss.xml",
            "http://feeds.bbci.co.uk/news/world/rss.xml",
        ],
    }

    # 3. Flatten the dictionary structure into a list of row records
    flat_data = [
        {"source_name": title, "rss_url": url}
        for title, urls in feeds_dict.items()
        for url in urls
    ]

    # 4. Marshal the records into a Pandas DataFrame
    df_to_seed = pd.DataFrame(flat_data)

    print("Clearing historical entries via truncation to allow a clean seed...")
    # Using RESTART IDENTITY resets our primary key counter back to 1
    db.execute_statement("TRUNCATE TABLE rss_sources RESTART IDENTITY CASCADE;")

    print(f"Writing {len(df_to_seed)} feed sources to the 'rss_sources' table...")
    # 5. Commit the DataFrame rows to the database
    db.write_df_to_psql("rss_sources", df_to_seed, if_exists="append")
    print("Database seeding completed successfully!")


if __name__ == "__main__":
    seed_initial_feeds()
