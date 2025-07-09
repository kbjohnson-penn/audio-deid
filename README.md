# Audio De-identification Tool

## Overview

The Audio De-identification Tool is a Python script designed to remove Protected Health Information (PHI) from audio tracks by replacing specified time intervals with beep sounds. It supports both audio-only files and video files with audio tracks.

## Prerequisites

- Python 3.x
- FFmpeg (required by moviepy for video processing)

## Installation

### Install Virtual Environment

```bash
pip install virtualenv
```

### Create and Activate Environment

```bash
python -m venv env
source env/bin/activate  # Use ".\env\Scripts\activate" on Windows
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

## Usage

The script is executed from the command line with the following parameters:

### Required Parameters

- `--source`: Path to the source audio or video file
- `--json`: Path to the JSON file containing PHI time intervals
- `--output`: Path where the scrubbed result will be saved

### Optional Parameters

- `--target_video`: Path to a different video file to reattach the scrubbed audio to
- `--log`: Enable detailed logging to file (logs saved in `logs/` directory)

### Usage Scenarios

#### 1. Audio-only Processing

Process an audio file and save scrubbed audio:

```bash
python scrub.py --source audio.mp3 --json phi_intervals.json --output scrubbed_audio.mp3 --log
```

#### 2. Video Processing (Same Video)

Extract audio from video, scrub it, and save as new video:

```bash
python scrub.py --source video.mp4 --json phi_intervals.json --output scrubbed_video.mp4 --log
```

#### 3. Video Processing (Different Target)

Extract audio from one video, scrub it, then attach to a different video:

```bash
python scrub.py --source original.mp4 --json phi_intervals.json --output final.mp4 --target_video processed.mp4 --log
```

This is useful when you have a video that's already been processed (e.g., face-blurred) and want to add the scrubbed audio to it.

## JSON Format Requirements

The JSON file must contain PHI time intervals in one of two formats:

### Format 1: Simple word_segments (Expected by the tool)

```json
{
  "word_segments": {
    "1": {
      "word": "**NAME**",
      "start": "12.5",
      "end": "15.2",
      "score": "0.95",
      "speaker": "SPEAKER_01"
    },
    "2": {
      "word": "**LOCATION**",
      "start": "28.1",
      "end": "29.8",
      "score": "0.87",
      "speaker": "SPEAKER_02"
    }
  }
}
```

### Format 2: Full transcript format

If your JSON file contains a full transcript with nested segments and words, the tool will automatically extract the `word_segments` section.

### JSON Field Descriptions

- `word`: The detected PHI text (words surrounded by `**` are processed)
- `start`: Start time in seconds (as string or float)
- `end`: End time in seconds (as string or float)
- `score`: Confidence score (optional)
- `speaker`: Speaker identifier (optional)

Only segments where the `word` field matches the pattern `**text**` will be replaced with beeps.

## Output

- **Audio processing**: Generates MP3 files with PHI segments replaced by beeps
- **Video processing**: Generates MP4 files with original video and scrubbed audio
- **Logging**: Optional detailed logs saved in the `logs/` directory with timestamps and processing information
  - Log files are named with timestamp: `log_YYYYMMDD_HHMMSS.log`
  - PHI content is sanitized in logs (shown as `[REDACTED]`)
  - Includes progress indicators and warnings for any issues

## Performance & Privacy Features

- **Memory Efficient**: Uses streaming audio processing to handle large files
- **Privacy Protected**: PHI words are replaced with `[REDACTED]` in all log outputs
- **Robust Error Handling**: Handles videos without audio tracks gracefully
- **Automatic Cleanup**: Temporary files are created in system temp directory and cleaned up
- **Overlap Detection**: Warns if PHI intervals overlap in the JSON file

## Supported Formats

- **Audio**: MP3, WAV, M4A, FLAC
- **Video**: MP4, AVI, MOV, MKV

## Notes

- The `beep.mp3` file must be present in the same directory as the script
- Temporary files are created in the system temp directory and automatically cleaned up
- Processing shows progress indicators (e.g., "Processing interval 1/37")
- Videos without audio tracks will raise an informative error
- All logs are organized in the `logs/` subdirectory for better file management

