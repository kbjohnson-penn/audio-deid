# Audio Scrubber

## Overview

The Audio Scrubber is a Python script designed to manipulate the audio track of a video file by inserting a "beep" sound at specified time intervals.

## Prerequisites

- Python 3.x

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

The script is executed from the command line and requires four arguments:

- `--source`: Path to the original video file.
- `--json`: Path to the JSON file containing time intervals.
- `--output`: Path to the scrubbed audio file.
- `--log`: Enable logging. This is optional.

### Script Execution

```bash
python scrub.py --source <source_video_path> --json <json_file_path> --output <output_audio_path> [--log]
```

Replace **<source_video_path>**, **<json_file_path>**, and **<output_audio_path>** with the paths to your source video file, JSON file, and output audio file, respectively. Include **--log** if you want to enable logging.
