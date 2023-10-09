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

Use the Philtered JSON files

Words that should be censored/beeped in the audio track should be surrounded by double asterisks **.

## Script Execution

The script is executed from the command line and requires four arguments:

- __video_file_path__: Path to the original video file.
- __beep_file_path__: Path to the beep sound file.
- __start_stop_timestamps_json__: Path to the JSON file containing word segments.
- __scrubbed_video_file_path__: Path to save the modified video file.

Execute the script using the following command:

```bash
python scrub.py <video_file_path> <beep_file_path> <start_stop_timestamps_json> <scrubbed_video_file_path>
```

Example:

```bash
python scrub.py sample_video.mp4 beep_sound.mp3 word_segments.json scrubbed_video.mp4
```

### Functions
- __get_start_end_timestamps(philtered_json)__: Extracts start and end timestamps of words to be beeped from a JSON file.
- __scrub_audio(source_video_path, beep_path, time_intervals, scrubbed_video_path)__: Scrubs the audio of the original video and inserts beep sounds at specified intervals.
- __seconds_to_minutes(time_data)__: Converts time data from seconds to minutes (not used in the main function but available for utility).
- __main()__: Main function that executes the script using command line arguments.

### To Deactivate Environment

```bash
deactivate
```
