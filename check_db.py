import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

db_url = os.environ.get('DATABASE_URL')
print(f"Testing connection to: {db_url}")

if db_url and db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+psycopg://")

try:
    engine = create_engine(db_url)
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        print("\nSUCCESS! Database connection established.")
        print(f"Connected to version: {connection.dialect.name}")
except Exception as e:
    print("\nFAILURE! Could not connect to the database.")
    print(f"Error: {e}")
    print("\nPlease checks your credentials in .env file.")
    print("Common issue: Username 'system' is usually wrong for PostgreSQL. Try 'postgres'.")
