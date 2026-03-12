import os
import sys
from utils.db import get_db
from dotenv import load_dotenv

# Ensure we are loading the local .env
load_dotenv(override=True)

print(f"Testing connection to: {os.getenv('MONGODB_URI', '').split('@')[-1]}")

try:
    # This should trigger the ping in MongoDBClient.__new__
    client_instance = get_db()
    db = client_instance.db
    if db is not None:
        print("✅ Python Backend: Database handle acquired successfully.")
        # Try a real operation
        colls = db.list_collection_names()
        print(f"✅ Python Backend: Successfully listed {len(colls)} collections.")
    else:
        print("❌ Python Backend: Database handle is None.")
except Exception as e:
    print(f"❌ Python Backend: Connection failed!")
    print(f"Error details: {e}")
