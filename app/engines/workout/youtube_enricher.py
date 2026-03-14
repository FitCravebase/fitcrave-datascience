import json
import logging
import time
from pathlib import Path
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
DB_PATH = Path(__file__).parent / "data" / "exercises.json"
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")

def get_youtube_video_id(exercise_name: str, youtube) -> str:
    """Search YouTube for the given exercise and return the top video ID."""
    try:
        # We append 'tutorial proper form' to improve search accuracy
        query = f"How to do {exercise_name} exercise proper form tutorial"
        
        request = youtube.search().list(
            part="snippet",
            maxResults=1,
            q=query,
            type="video",
            videoDuration="short" # Prefer shorter videos
        )
        response = request.execute()

        if response.get("items"):
            return response["items"][0]["id"]["videoId"]
        return None
    except HttpError as e:
        logger.error(f"YouTube API error for {exercise_name}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error for {exercise_name}: {e}")
        return None

def enrich_database():
    """Iterate through the database, fetch video IDs, and save back to JSON."""
    if not YOUTUBE_API_KEY or YOUTUBE_API_KEY == "your_youtube_api_key_here":
        logger.error("No valid YOUTUBE_API_KEY found in .env. Exiting.")
        return

    if not DB_PATH.exists():
        logger.error(f"Could not find exercises database at {DB_PATH}")
        return

    # Initialize YouTube client
    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

    # Load Database
    with open(DB_PATH, "r", encoding="utf-8") as f:
        exercises = json.load(f)

    logger.info(f"Loaded {len(exercises)} exercises. Starting enrichment...")
    
    updated_count = 0
    
    # Process exercises
    for i, ex in enumerate(exercises):
        if "video_id" not in ex or ex["video_id"] is None:
            logger.info(f"[{i+1}/{len(exercises)}] Searching for: {ex['name']}...")
            video_id = get_youtube_video_id(ex["name"], youtube)
            
            ex["video_id"] = video_id
            updated_count += 1
            
            # Save progressively every 50 requests in case of a crash or rate limit
            if updated_count % 50 == 0:
                with open(DB_PATH, "w", encoding="utf-8") as f:
                    json.dump(exercises, f, indent=2)
                logger.info(f"--- Saved progress ({updated_count} new updates) ---")
            
            # Sleep to respect rate limits (YouTube allows ~10k units/day, search costs 100 units)
            # This means we can do ~100 queries a day on the free tier.
            # We should probably stop if we get a quota error.
            time.sleep(1)

    # Final Save
    if updated_count > 0:
        with open(DB_PATH, "w", encoding="utf-8") as f:
            json.dump(exercises, f, indent=2)
        logger.info(f"Finished! Successfully added {updated_count} new video IDs.")
    else:
        logger.info("Database is already fully enriched!")

if __name__ == "__main__":
    enrich_database()
