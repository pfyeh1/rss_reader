import os
import psycopg2 as psql
import sqlalchemy
import pandas as pd

class ReplitPgHandler:
    def __init__(self):
        """
        Initializes connection parameters by reading directly from 
        the system environment variables provided by the platform.
        """
        self.user = os.environ.get('DB_USER')
        self.password = os.environ.get('DB_PASSWORD')
        self.host = os.environ.get('DB_HOST')
        self.port = os.environ.get('DB_PORT', '5432')
        self.database = os.environ.get('DB_NAME')
        
        # Verify that mandatory configuration items exist
        if not all([self.user, self.password, self.host, self.database]):
            raise ValueError("Missing mandatory database environment variables!")

    def create_connection(self):
        """Creates a raw psycopg2 connection instance."""
        try:
            return psql.connect(
                user=self.user,
                password=self.password,
                host=self.host,
                port=self.port,
                database=self.database
            )
        except Exception as error:
            print(f"Database raw connection error: {error}")
            return None

    def generate_engine(self):
        """Generates a SQLAlchemy engine connection pool for Pandas operations."""
        url = f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
        return sqlalchemy.create_engine(url)

    def execute_statement(self, statement):
        """Executes a single structural or data modification SQL action."""
        connection = self.create_connection()
        if not connection:
            return
        cursor = connection.cursor()
        try:
            cursor.execute(statement)
            connection.commit()
        finally:
            cursor.close()
            connection.close()

    def read_sql_to_pd(self, sql_statement):
        """Queries the database and marshals records into a Pandas DataFrame."""
        engine = self.generate_engine() 
        try:
            return pd.read_sql(sql_statement, engine)
        except Exception as e:
            print(f"Error executing database query read: {e}")
            return None
        finally:
            engine.dispose()

    def write_df_to_psql(self, table_name, df, if_exists='append'):
        """Appends a Pandas DataFrame cleanly to the specified target database table."""
        engine = self.generate_engine()
        try:
            df.to_sql(
                table_name,
                engine,
                if_exists=if_exists,
                index=False,
                method="multi",
                chunksize=1000
            )
            print(f"Successfully committed {len(df)} records to table '{table_name}'.")
        except Exception as e:
            print(f"Error writing DataFrame data to database: {e}")
            raise e
        finally:
            engine.dispose()
