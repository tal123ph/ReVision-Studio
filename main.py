# -*- coding: utf-8 -*-
import os
import asyncio
import aiohttp
import yt_dlp
from pathlib import Path
from dotenv import load_dotenv
from supadata import Supadata
from decart import DecartClient
from decart import models as decart_models
from decart.process import send_request

load_dotenv()

# Available styles for the user to choose from
STYLES = {
    "1": "cyberpunk city, neon lights, high contrast, futuristic",
    "2": "Studio Ghibli animation style, soft colors, whimsical",
    "3": "van gogh oil painting style, swirling brushstrokes, vivid",
    "4": "GTA game style, comic shading, vibrant colors",
    "5": "pencil sketch, monochrome, charcoal drawing style",
}


def fetch_video_info(video_url: str) -> dict:
    """Use Supadata to fetch YouTube video metadata."""
    api_key = os.getenv("SUPADATA_API_KEY")
    if not api_key:
        raise ValueError("SUPADATA_API_KEY not set in .env")
    sd = Supadata(api_key=api_key)
    info = sd.youtube.video(video_url)  # positional arg, not keyword
    # info may be an object or dict depending on supadata version
    if hasattr(info, "__dict__"):
        info = vars(info)
    return info if isinstance(info, dict) else {}


def download_video(video_url: str, output_path: str = "input_video.mp4") -> str:
    """Download the YouTube video using yt-dlp."""
    print("Downloading video...")
    ydl_opts = {
        # Use a single pre-merged stream -- no ffmpeg required
        "format": "best[ext=mp4]/best",
        "outtmpl": output_path,
        "quiet": True,
        "no_warnings": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_url])
    print("Downloaded to: " + output_path)
    return output_path


async def restyle_video(
    video_path: str, style_prompt: str, output_path: str = "restyled_output.mp4"
) -> str:
    """Send the video to Decart's lucy-pro-v2v model for restyling."""
    decart_key = os.getenv("DECART_API_KEY")
    if not decart_key:
        raise ValueError("DECART_API_KEY not set in .env")

    client = DecartClient(api_key=decart_key)
    model = decart_models.video("lucy-pro-v2v")

    print("\nSending video to Decart for restyling...")
    print("Style: " + style_prompt)

    async with aiohttp.ClientSession() as session:
        result_bytes = await send_request(
            session=session,
            base_url=client.base_url,
            api_key=client.api_key,
            model=model,
            inputs={
                "data": Path(video_path),
                "prompt": style_prompt,
            },
        )

    with open(output_path, "wb") as f:
        f.write(result_bytes)

    print("Restyled video saved to: " + output_path)
    return output_path


def select_style() -> str:
    """Interactive style selection."""
    print("\nAvailable Styles:")
    for key, style in STYLES.items():
        print(f"  [{key}] {style}")
    print("  [c] Custom (enter your own prompt)")

    choice = input("\nSelect a style: ").strip().lower()

    if choice == "c":
        return input("Enter your style prompt: ").strip()
    elif choice in STYLES:
        return STYLES[choice]
    else:
        print("Invalid choice, defaulting to Cyberpunk.")
        return STYLES["1"]


async def main():
    print("=" * 50)
    print("  Vision Agents -- Decart Video Restyler")
    print("=" * 50)

    video_url = input("\nEnter YouTube video URL: ").strip()
    if not video_url:
        print("No URL provided. Exiting.")
        return

    # 1. Fetch video info via Supadata
    title = "video"
    try:
        info = fetch_video_info(video_url)
        title = info.get("title", "video") or "video"
        print("\nVideo: " + title)
    except Exception as e:
        print("Could not fetch video info via Supadata: " + str(e))
        print("Continuing with download...")

    # 2. Select style
    style_prompt = select_style()

    # 3. Download the video
    safe_title = "".join(c for c in title if c.isalnum() or c in " _-")[:40].strip()
    input_path = f"input_{safe_title}.mp4"
    output_path = f"restyled_{safe_title}.mp4"

    try:
        download_video(video_url, input_path)
    except Exception as e:
        print("Failed to download video: " + str(e))
        return

    # 4. Restyle with Decart
    try:
        result = await restyle_video(input_path, style_prompt, output_path)
        print("\nDone! Your restyled video is ready: " + result)
    except Exception as e:
        print("Decart restyling failed: " + str(e))
        return

    # 5. Cleanup input file
    try:
        Path(input_path).unlink()
    except Exception:
        pass


if __name__ == "__main__":
    asyncio.run(main())
