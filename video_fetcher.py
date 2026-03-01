import os
from dotenv import load_dotenv
from supadata import Supadata

load_dotenv()

def fetch_youtube_video_info(video_url: str):
    api_key = os.getenv("SUPADATA_API_KEY")
    if not api_key:
        raise ValueError("SUPADATA_API_KEY not found in .env file")
    
    sd = Supadata(api_key=api_key)
    
    try:
        # Fetch metadata for the video
        metadata = sd.youtube.video(url=video_url)
        print(f"Fetched metadata for: {metadata.get('title', 'Unknown Title')}")
        return metadata
    except Exception as e:
        print(f"Error fetching video info: {e}")
        return None

if __name__ == "__main__":
    # Test with a sample video URL if provided or a default one
    sample_url = "https://www.youtube.com/watch?v=aqz-KE-bpKQ" # Example video
    info = fetch_youtube_video_info(sample_url)
    if info:
        print(info)
