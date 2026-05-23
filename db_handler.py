import os
import psycopg2 as psql
import sqlalchemy
import pandas as pd


class ReplitPgHandler:
    def __init__(self):
        """
        Initializes connection parameters from environment variables.
        Supports both DB_* (custom) and PG* (Replit-managed) variable names.
        """
        self.user = os.environ.get("DB_USER") or os.environ.get("PGUSER")
        self.password = os.environ.get("DB_PASSWORD") or os.environ.get("PGPASSWORD")
        self.host = os.environ.get("DB_HOST") or os.environ.get("PGHOST")
        self.port = os.environ.get("DB_PORT") or os.environ.get("PGPORT", "5432")
        self.database = os.environ.get("DB_NAME") or os.environ.get("PGDATABASE")

        if not all([self.user, self.password, self.host, self.database]):
            raise ValueError("Missing mandatory database environment variables!")

    def create_connection(self):
        """Creates and returns a raw psycopg2 connection. Raises on failure."""
        return psql.connect(
            user=self.user,
            password=self.password,
            host=self.host,
            port=self.port,
            database=self.database,
        )

    def generate_engine(self):
        """Generates a SQLAlchemy engine for Pandas operations."""
        url = f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
        return sqlalchemy.create_engine(url)

    def execute_statement(self, statement):
        """Executes a single SQL statement (DDL or DML)."""
        connection = self.create_connection()
        cursor = connection.cursor()
        try:
            cursor.execute(statement)
            connection.commit()
        finally:
            cursor.close()
            connection.close()

    def read_sql_to_pd(self, sql_statement):
        """Queries the database and returns results as a Pandas DataFrame, or None on error."""
        engine = self.generate_engine()
        try:
            return pd.read_sql(sql_statement, engine)
        except Exception as e:
            print(f"Error executing database query: {e}")
            return None
        finally:
            engine.dispose()

    def write_df_to_psql(self, table_name, df, if_exists="append"):
        """Writes a Pandas DataFrame to the specified database table."""
        engine = self.generate_engine()
        try:
            df.to_sql(
                table_name,
                engine,
                if_exists=if_exists,
                index=False,
                method="multi",
                chunksize=1000,
            )
            print(f"Successfully committed {len(df)} records to table '{table_name}'.")
        except Exception as e:
            print(f"Error writing DataFrame to database: {e}")
            raise
        finally:
            engine.dispose()
