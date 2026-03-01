# 🎬 Vision Agents – Decart & Supadata Video Restyling

An AI-powered system that fetches a YouTube video and restyles it in real time using Vision Agents with the Decart plugin.

---

## 🚀 Project Overview

This project integrates:

- Supadata → Fetch YouTube metadata or stream URL
- Vision Agents → AI agent orchestration
- Decart Plugin → Apply AI-based video restyling
- Stream → Real-time transport layer

The user provides a YouTube link, selects a style (e.g., GTA, Cyberpunk, Animated), and receives a restyled version of the video.

---

## 🧠 System Architecture

User → UI → Supadata → Vision Agent → Decart Plugin → Restyled Video Output

### Flow:

1. User enters YouTube URL.
2. Supadata fetches video metadata or stream URL.
3. Vision Agent processes the video input.
4. Decart applies selected AI restyling.
5. Restyled video is streamed back to UI.

---

## 📁 Project Structure

project-root/
│
├── .env
├── video_fetcher.py
├── vision_agent.py
├── main.py
├── try_mirage.py
├── requirements.txt
└── README.md


---

## ⚙️ Configuration

Create a `.env` file in the root directory:


SUPADATA_API_KEY=your_supadata_key
DECART_API_KEY=your_decart_key


### API Keys Required

- SUPADATA_API_KEY → Fetch YouTube metadata
- DECART_API_KEY → Apply AI video restyling
- STREAM_API_KEY → Required for Vision Agents real-time transport

---

## 🖥 Backend Components

### 1️⃣ video_fetcher.py

Responsible for:
- Accepting YouTube URL
- Calling Supadata API
- Returning video stream URL or metadata

---

### 2️⃣ vision_agent.py

Responsible for:
- Initializing Vision Agent
- Loading Decart plugin
- Passing video stream to Decart
- Applying selected restyling style

Example styles:
- GTA
- Cyberpunk
- Animated
- Cartoon
- Neon

---

## 🎨 Frontend (index.html) not added yet

Features:
- Input field for YouTube URL
- Dropdown menu for style selection
- Submit button
- Video player to display restyled output

---

## 🧪 Verification Plan

### Manual Testing Steps

1. Start backend server.
2. Open index.html.
3. Paste a YouTube video URL.
4. Select a style (e.g., Cyberpunk).
5. Click "Restyle Video".
6. Confirm:
   - Video loads successfully.
   - Style is visibly applied.
   - Output streams smoothly (if real-time enabled).

---

## 🏆 Key Features

- Real-time AI video transformation
- Plugin-based Vision Agent architecture
- Modular backend design
- Expandable to new styles
- API-driven integration

---

## 🔮 Future Improvements

- Add style intensity slider
- Add before/after comparison mode
- Add downloadable restyled video
- Add user authentication
- Add caching for processed videos

---

## 📦 Installation

Create virtual environment:

```bash
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt

