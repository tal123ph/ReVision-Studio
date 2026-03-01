# -*- coding: utf-8 -*-
"""
try_mirage.py
Use Decart mirage_v2 real-time model on a downloaded YouTube video.

Pipeline:
  1. Supadata: fetch video title
  2. yt-dlp: download YouTube video
  3. aiortc + av: read video frames and create a fake local VideoStreamTrack
  4. Decart RealtimeClient (mirage_v2): transform frames in real-time
  5. Write output frames to restyled .mp4 file
"""
import asyncio
import os
import fractions
import time
import av
import yt_dlp
from pathlib import Path
from dotenv import load_dotenv
from supadata import Supadata
from aiortc import VideoStreamTrack
from aiortc.mediastreams import MediaStreamError
from av import VideoFrame
from decart import DecartClient, models as decart_models
from decart.types import ModelState, Prompt
from decart.realtime import RealtimeClient, RealtimeConnectOptions

load_dotenv()

STYLES = {
    "1": "cyberpunk city, neon lights, high contrast, futuristic",
    "2": "Studio Ghibli animation style, soft colors, whimsical",
    "3": "van gogh oil painting style, swirling brushstrokes, vivid",
    "4": "GTA game style, comic shading, vibrant colors",
    "5": "pencil sketch, monochrome, charcoal drawing style",
}


class FileVideoTrack(VideoStreamTrack):
    """aiortc VideoStreamTrack that reads frames from a video file."""

    kind = "video"

    def __init__(self, file_path: str, model_fps: int = 22,
                 model_width: int = 1280, model_height: int = 704):
        super().__init__()
        self._container = av.open(file_path)
        self._stream = self._container.streams.video[0]
        self._stream.thread_type = "AUTO"
        self._frames = self._container.decode(self._stream)
        self._model_fps = model_fps
        self._model_width = model_width
        self._model_height = model_height
        self._timestamp = 0
        self._time_base = fractions.Fraction(1, model_fps)

    async def recv(self) -> VideoFrame:
        try:
            frame = next(self._frames)
        except StopIteration:
            raise MediaStreamError("End of video file")

        # Resize to model dimensions
        img = frame.to_image()
        img = img.resize((self._model_width, self._model_height))
        new_frame = VideoFrame.from_image(img)
        new_frame.pts = self._timestamp
        new_frame.time_base = self._time_base
        self._timestamp += 1

        # Throttle to model fps
        await asyncio.sleep(1.0 / self._model_fps)
        return new_frame

    def stop(self):
        self._container.close()
        super().stop()


def fetch_video_info(video_url: str) -> dict:
    api_key = os.getenv("SUPADATA_API_KEY")
    if not api_key:
        raise ValueError("SUPADATA_API_KEY not set in .env")
    sd = Supadata(api_key=api_key)
    info = sd.youtube.video(video_url)
    if hasattr(info, "__dict__"):
        info = vars(info)
    return info if isinstance(info, dict) else {}


def download_video(video_url: str, output_path: str) -> str:
    print("Downloading video...")
    ydl_opts = {
        "format": "best[ext=mp4]/best",
        "outtmpl": output_path,
        "quiet": True,
        "no_warnings": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_url])
    print("Downloaded to: " + output_path)
    return output_path


def select_style() -> str:
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


async def restyle_with_mirage(input_path: str, style_prompt: str, output_path: str,
                               duration_seconds: int = 30):
    decart_key = os.getenv("DECART_API_KEY")
    if not decart_key:
        raise ValueError("DECART_API_KEY not set in .env")

    model_def = decart_models.realtime("mirage_v2")
    client = DecartClient(api_key=decart_key)

    # Output video writer
    output_container = av.open(output_path, mode="w")
    out_stream = output_container.add_stream("libx264", rate=model_def.fps)
    out_stream.width = model_def.width
    out_stream.height = model_def.height
    out_stream.pix_fmt = "yuv420p"
    frames_written = [0]
    done_event = asyncio.Event()

    def on_remote_stream(transformed_track):
        print("Receiving transformed frames from Decart mirage_v2...")
        asyncio.create_task(capture_frames(transformed_track))

    async def capture_frames(track):
        try:
            while not done_event.is_set():
                frame = await track.recv()
                # Write frame to output file
                for pkt in out_stream.encode(frame):
                    output_container.mux(pkt)
                frames_written[0] += 1
                if frames_written[0] % (model_def.fps * 5) == 0:
                    print(f"  Captured {frames_written[0]} frames...")
        except Exception:
            pass
        finally:
            done_event.set()

    local_track = FileVideoTrack(
        input_path,
        model_fps=model_def.fps,
        model_width=model_def.width,
        model_height=model_def.height,
    )

    print(f"\nConnecting to Decart mirage_v2...")
    print(f"Style: {style_prompt}")

    initial_state = ModelState(
        prompt=Prompt(text=style_prompt, enrich=True),
        mirror=False,
    )

    realtime_client = await RealtimeClient.connect(
        base_url=client.base_url,
        api_key=client.api_key,
        local_track=local_track,
        options=RealtimeConnectOptions(
            model=model_def,
            on_remote_stream=on_remote_stream,
            initial_state=initial_state,
        ),
    )

    print(f"Connected! Processing for up to {duration_seconds} seconds...")
    try:
        await asyncio.wait_for(done_event.wait(), timeout=duration_seconds)
    except asyncio.TimeoutError:
        print(f"Stopping after {duration_seconds}s ({frames_written[0]} frames captured).")

    await realtime_client.disconnect()
    local_track.stop()

    # Flush and close output
    for pkt in out_stream.encode():
        output_container.mux(pkt)
    output_container.close()

    print(f"Done! Restyled video saved to: {output_path}")
    return output_path


async def main():
    print("=" * 50)
    print("  Decart mirage_v2 Real-Time Restyler")
    print("=" * 50)

    video_url = input("\nEnter YouTube video URL: ").strip()
    if not video_url:
        print("No URL provided. Exiting.")
        return

    # 1. Supadata metadata
    title = "video"
    try:
        info = fetch_video_info(video_url)
        title = info.get("title", "video") or "video"
        print("\nVideo: " + title)
    except Exception as e:
        print("Supadata warning: " + str(e))

    # 2. Select style
    style_prompt = select_style()

    # 3. Download
    safe_title = "".join(c for c in title if c.isalnum() or c in " _-")[:40].strip()
    input_path = f"input_{safe_title}.mp4"
    output_path = f"mirage_{safe_title}.mp4"

    try:
        download_video(video_url, input_path)
    except Exception as e:
        print("Download failed: " + str(e))
        return

    # 4. Restyle with mirage_v2
    duration = int(input("\nHow many seconds to process? (default 30): ").strip() or "30")

    try:
        await restyle_with_mirage(input_path, style_prompt, output_path, duration)
    except Exception as e:
        print("Mirage restyling failed: " + str(e))
        return

    # 5. Cleanup
    try:
        Path(input_path).unlink()
    except Exception:
        pass


if __name__ == "__main__":
    asyncio.run(main())
