from sqlalchemy import text
from db import engine

print("Testing database connection...")

try:
    with engine.connect() as connection:
        result = connection.execute(text("SELECT DATABASE()"))
        print("Connected successfully!")
        print("Database:", result.scalar())

except Exception as e:
    print("Connection failed:", repr(e))