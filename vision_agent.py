import os
import asyncio
from dotenv import load_dotenv
from vision_agents import Agent, Plugin
from vision_agents.plugins.decart import DecartPlugin
from video_fetcher import fetch_youtube_video_info

load_dotenv()

async def start_restyling_agent(video_url: str, style_prompt: str):
    stream_api_key = os.getenv("STREAM_API_KEY")
    decart_api_key = os.getenv("DECART_API_KEY")
    
    if not all([stream_api_key, decart_api_key]):
        print("Missing API keys in .env file.")
        return

    # 1. Fetch video info (for context/preview)
    video_info = fetch_youtube_video_info(video_url)
    if not video_info:
        print("Could not retrieve video information.")
        return

    print(f"Starting restyling for: {video_info.get('title')}")

    # 2. Initialize Vision Agent with Decart Plugin
    # Note: Precise Vision Agents SDK usage might vary based on latest version
    # This follows the general pattern suggested by documentation
    
    decart = DecartPlugin(api_key=decart_api_key)
    
    agent = Agent(
        plugins=[decart],
        api_key=stream_api_key
    )

    # 3. Connect video source and apply restyling
    # The Decart plugin typically restyles the live video stream.
    # For a YouTube video, we might need to stream it as input.
    
    print(f"Applying style: {style_prompt}")
    
    # Placeholder for actual stream connection logic
    # In a real app, this would be tied to a WebRTC session or local media capture
    # Here we are setting up the agent configuration
    
    await agent.run(
        input_video=video_url, # Assuming direct URL support or handled by a source plugin
        style=style_prompt
    )

if __name__ == "__main__":
    test_url = "https://www.youtube.com/watch?v=aqz-KE-bpKQ"
    test_style = "cyberpunk aesthetic, neon lights, night city"
    
    asyncio.run(start_restyling_agent(test_url, test_style))
