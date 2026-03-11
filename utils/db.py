import os
import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from dotenv import load_dotenv

# Load environment variables just in case this is run independently
# Use override=True so cached values in the virtual env are flushed by actual .env contents
load_dotenv(override=True)

MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("DB_NAME", "fitcrave")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "conversations")

logger = logging.getLogger(__name__)

class MongoDBClient:
    _instance = None
    _client = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDBClient, cls).__new__(cls)
            try:
                if MONGODB_URI:
                    cls._client = MongoClient(MONGODB_URI)
                    # Verify connection
                    cls._client.admin.command('ping')
                    logger.info("Successfully connected to MongoDB")
                else:
                    logger.warning("MONGODB_URI is not set. Database connection skipped.")
            except ConnectionFailure as e:
                logger.error(f"Failed to connect to MongoDB: {e}")
                cls._client = None
        return cls._instance

    @property
    def db(self):
        if self._client:
            return self._client[DB_NAME]
        return None

    @property
    def conversations_collection(self):
        db = self.db
        if db is not None:
            return db[COLLECTION_NAME]
        return None

def get_db():
    return MongoDBClient()

def push_conversation(session_id: str, user_id: str, message: dict, agent_data: dict = None):
    """
    Pushes a conversation turn into the MongoDB collection.
    If a document with the session_id exists, it appends to a messages array.
    If not, it creates a new document.
    """
    db_client = get_db()
    collection = db_client.conversations_collection
    
    if collection is None:
        logger.error("Could not get conversations collection. DB not connected.")
        return False
        
    try:
        # Deduplication: check if the last stored message is already the same content + type
        existing_doc = collection.find_one({"session_id": session_id, "user_id": user_id})
        if existing_doc:
            existing_messages = existing_doc.get("messages", [])
            if existing_messages:
                last_stored = existing_messages[-1]
                if (last_stored.get("content") == message.get("content") and
                    last_stored.get("type") == message.get("type")):
                    logger.debug(f"Skipping duplicate message for session {session_id}: '{message.get('content')[:50]}'")
                    return True
        
        # Upsert: update existing session or insert new one
        result = collection.update_one(
            {"session_id": session_id, "user_id": user_id},
            {
                "$push": {"messages": message},
                "$set": {
                    "last_updated": "current_timestamp_placeholder", # We can use python datetime here later
                    "agent_data": agent_data or {}
                }
            },
            upsert=True
        )
        return True
    except Exception as e:
        logger.error(f"Error pushing conversation to MongoDB: {e}")
        return False

def get_conversation_history(session_id: str, user_id: str, limit: int = 10) -> list:
    """
    Fetches the last N messages from a specific session in MongoDB.
    Returns a list of dictionary formats: [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
    """
    db_client = get_db()
    collection = db_client.conversations_collection
    
    if collection is None:
        logger.error("Could not get conversations collection. DB not connected.")
        return []
        
    try:
        # Find the single document matching the session_id
        session_doc = collection.find_one({"session_id": session_id, "user_id": user_id})
        
        if not session_doc or "messages" not in session_doc:
            return []
            
        messages = session_doc.get("messages", [])
        
        # We rely on MongoDB's natural array insertion order. Do not sort by sequence_number
        # because sequence_number resets per request/turn, ruining the timeline.
        recent_messages = messages[-limit:] if len(messages) > limit else messages
        
        # Convert internal DB format to a cleaner universal format for LangChain prompt generation
        formatted_history = []
        for msg in recent_messages:
            msg_type = msg.get("type", "human")
            role = "user" if msg_type == "human" else "assistant"
            formatted_history.append({
                "role": role,
                "content": msg.get("content", "")
            })
            
        return formatted_history
        
    except Exception as e:
        logger.error(f"Error fetching conversation history from MongoDB for session {session_id}: {e}")
        return []
