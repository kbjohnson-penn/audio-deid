import argparse
import json
import logging
from datetime import datetime
import pandas as pd
from pydub import AudioSegment
import os
from moviepy.editor import VideoFileClip, AudioFileClip
import uuid

def transform_json_schema(input_json_file):
    """
    Transform the JSON schema to the expected format.
    
    Args:
    input_json_file (str): Path to the input JSON file.
    
    Returns:
    transformed_data (dict): Transformed JSON data.
    """
    try:
        # Load the original JSON data
        with open(input_json_file, 'r') as f:
            original_data = json.load(f)

        # Transform the data to the expected schema
        transformed_data = {
            "word_segments": []
        }

        word_segments = original_data.get("word_segments")
        for word_segment in word_segments:
            transformed_data["word_segments"].append({
                "word": word_segments[word_segment].get("word", ""),
                "start": word_segments[word_segment].get("start", ""),
                "end": word_segments[word_segment].get("end", ""),
                "score": word_segments[word_segment].get("score", ""),
                "speaker": word_segments[word_segment].get("speaker", "")
            })

        return transformed_data

    except Exception as e:
        print(f"Error transforming JSON schema: {e}")

def get_start_end_timestamps(philtered_json):
    """
    Extract start and end timestamps from the JSON data.
    
    Args:
    philtered_json (dict): JSON data containing word segments.
    
    Returns:
    list: List of dictionaries containing start and end timestamps.
    """
    try:
        # Check if "word_segments" exists and is a list
        if "word_segments" not in philtered_json:
            raise KeyError("Key 'word_segments' not found in JSON data.")

        # Convert JSON data to DataFrame for easier manipulation
        word_segments_df = pd.DataFrame(philtered_json["word_segments"])

        print("Columns in DataFrame:", word_segments_df.columns)
        
        # Filter rows that contain the pattern
        filtered_df = word_segments_df[word_segments_df['word'].str.contains(
            r'\*\*\w+\*\*', regex=True, na=False)]

        # Convert filtered data to list of dictionaries
        filtered_json = filtered_df[['start', 'end']].to_dict(orient='records')

        # Filter out invalid intervals
        valid_intervals = [
            interval for interval in filtered_json
            if pd.notna(interval['start']) and pd.notna(interval['end']) and float(interval['start']) < float(interval['end'])
        ]

        logging.info('Converted filtered data to list of dictionaries')

        return valid_intervals

    except Exception as e:
        logging.error('Error occurred while loading JSON data: %s', e)
        raise


def scrub_audio(source_path, time_intervals, scrubbed_audio_path, target_video_path=None):
    """
    Scrub audio from an audio or video file and replace segments with beeps.
    
    Args:
    source_path (str): Path to the source audio or video file.
    time_intervals (list): List of dictionaries containing start and end timestamps.
    scrubbed_audio_path (str): Path to the scrubbed audio or video file.
    target_video_path (str): Path to a different video file to reattach the scrubbed audio.
    
    Raises:
    FileNotFoundError: If the beep file is not found.
    ValueError: If the scrubbed_audio_path does not have a video-compatible extension.
    """
    try:
        # Generate unique filenames for temporary files
        temp_audio_file = f"temp_audio_{uuid.uuid4()}.mp3"
        temp_scrubbed_audio_file = f"temp_scrubbed_audio_{uuid.uuid4()}.mp3"

        # Check if the source is a video
        is_video = source_path.lower().endswith(('.mp4', '.avi', '.mov', '.mkv'))
        audio = None

        # Load audio from video or audio file
        if is_video:
            with VideoFileClip(source_path) as video:
                video.audio.write_audiofile(temp_audio_file, codec="mp3")
                audio = AudioSegment.from_file(temp_audio_file)
                logging.info('Loaded video and extracted audio.')
        else:
            audio = AudioSegment.from_file(source_path)
            logging.info('Loaded audio file.')

        # Check if beep file exists
        if not os.path.isfile("beep.mp3"):
            raise FileNotFoundError("Beep file 'beep.mp3' not found.")

        # Load the beep sound
        beep = AudioSegment.from_file("beep.mp3")

        segments = []
        last_end_time = 0

        for interval in time_intervals:
            # Convert start and end times to milliseconds
            start_time = int(float(interval['start']) * 1000)
            end_time = int(float(interval['end']) * 1000)

            logging.info(
                'Processing interval: start_time=%s, end_time=%s', start_time, end_time)

            # Add the audio segment before the interval
            segments.append(audio[last_end_time:start_time])

            interval_duration = end_time - start_time

            # Add the beep segment
            if beep.duration_seconds * 1000 < interval_duration:
                loops = (interval_duration //
                         int(beep.duration_seconds * 1000)) + 1
                beep_segment = beep * loops
                beep_segment = beep_segment[:interval_duration]
            else:
                beep_segment = beep[:interval_duration]

            segments.append(beep_segment)
            last_end_time = end_time

        # Add the remaining audio after the last interval
        segments.append(audio[last_end_time:])

        # Concatenate all segments
        scrubbed_audio = sum(segments)

        # Export scrubbed audio to a unique temporary file
        scrubbed_audio.export(temp_scrubbed_audio_file, format="mp3")

        # If a target video path is provided, reattach the scrubbed audio to it
        if target_video_path:
            with VideoFileClip(target_video_path) as target_video:
                scrubbed_audio_clip = AudioFileClip(temp_scrubbed_audio_file)
                target_video = target_video.set_audio(scrubbed_audio_clip)

                # Check that output path has a video-compatible extension
                if not scrubbed_audio_path.lower().endswith(('.mp4', '.mov', '.avi', '.mkv')):
                    raise ValueError("scrubbed_audio_path should have a video-compatible extension like .mp4 or .mov")

                # Write the final video with audio
                target_video.write_videofile(
                    scrubbed_audio_path, codec="libx264", audio_codec="aac"
                )
                logging.info('Saved scrubbed video with reattached audio to %s', scrubbed_audio_path)
        else:
            # If no target video path, save scrubbed audio directly
            scrubbed_audio.export(scrubbed_audio_path, format="mp3")
            logging.info('Saved scrubbed audio to %s', scrubbed_audio_path)

        # Clean up temporary files
        os.remove(temp_audio_file)
        os.remove(temp_scrubbed_audio_file)

    except Exception as e:
        logging.error('Error occurred while scrubbing audio: %s', e)
        raise


def main():
    parser = argparse.ArgumentParser(
        description='Scrub audio from an audio or video file and replace segments with beeps.')
    parser.add_argument('--source', required=True,
                        help='Path to the source audio or video file.')
    parser.add_argument('--json', required=True,
                        help='Path to the JSON file containing time intervals.')
    parser.add_argument('--output', required=True,
                        help='Path to the scrubbed audio or video file.')
    parser.add_argument(
        '--target_video', help='Path to a different video file to reattach the scrubbed audio.')
    parser.add_argument('--log', action='store_true', help='Enable logging.')

    args = parser.parse_args()

    if args.log:
        log_filename = f"log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        logging.basicConfig(filename=log_filename, level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s')

    # Validate paths
    if not os.path.isfile(args.source):
        raise FileNotFoundError(f"Source file '{args.source}' not found.")
    if not os.path.isfile(args.json):
        raise FileNotFoundError(f"JSON file '{args.json}' not found.")
    if args.target_video and not os.path.isfile(args.target_video):
        raise FileNotFoundError(f"Target video file '{args.target_video}' not found.")

    # Transform the JSON schema
    transformed_json = transform_json_schema(args.json)
    
    # Get the start and end timestamps from the JSON file
    filtered_json = get_start_end_timestamps(transformed_json)
    logging.info('Filtered JSON: %s', filtered_json)

    # Scrub the audio and write to file
    scrub_audio(args.source, filtered_json, args.output, args.target_video)
    logging.info('Audio scrub completed.')


if __name__ == "__main__":
    main()
