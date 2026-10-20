
# Voicera

Voicera is a video dubbing system that translates educational videos into Indian languages with natural-sounding voices and perfect audio synchronization.

## Features

- **Multi-language Support**: Hindi, Tamil, Telugu, Kannada, Malayalam, English.
- **Natural Voices**: Uses Microsoft Edge TTS for human-like speech.
- **Technical Term Preservation**: Keeps programming and technical terms in English.
- **Audio Sync**: Adjusts tempo to match original video timing.
- **Modern UI**: Clean, responsive interface for easy uploads.

## Prerequisites

1.  **System Requirements**:
    *   Python 3.9+
    *   FFmpeg (Required for audio/video processing)

    **Install FFmpeg on Mac:**
    ```bash
    brew install ffmpeg
    ```

## Installation

1.  **Clone job setup:**
    (You are likely already in the directory)
    ```bash
    cd voicera
    ```

2.  **Create a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Running the Application

1.  **Start the Flask Server:**
    ```bash
    python app.py
    ```

2.  **Access the Web Interface:**
    Open your browser and navigate to: [http://localhost:5001](http://localhost:5001)

## Usage

1.  Upload an educational video (MP4, MOV, AVI).
2.  Select the target language (e.g., Hindi) and voice gender.
3.  Wait for processing (Audio extraction, transcription, translation, TTS, sync).
4.  Download the dubbed video.

## Directory Structure

- `app.py`: Main entry point.
- `processors/`: Core logic for audio, video, text processing.
- `utils/`: Configuration and helpers.
- `templates/`: HTML frontend.
- `uploads/`: Temporary storage for uploaded videos.
- `outputs/`: Storage for processed videos.
