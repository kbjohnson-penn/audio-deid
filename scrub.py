import argparse
import json
import logging
from datetime import datetime
from pydub import AudioSegment
import os
from moviepy.editor import VideoFileClip, AudioFileClip
import tempfile
import re

# Constants
MS_PER_SECOND = 1000
SUPPORTED_VIDEO_FORMATS = ('.mp4', '.avi', '.mov', '.mkv')
SUPPORTED_AUDIO_FORMATS = ('.mp3', '.wav', '.m4a', '.flac')
PHI_PATTERN = r'\*\*\w+\*\*'


def transform_json_schema(input_json_file):
    """
    Transform the JSON schema to the expected format.
    
    Args:
        input_json_file (str): Path to the input JSON file.
    
    Returns:
        dict: Original JSON data with word_segments.
    
    Raises:
        FileNotFoundError: If the JSON file doesn't exist.
        json.JSONDecodeError: If the JSON is invalid.
        KeyError: If required keys are missing.
    """
    try:
        with open(input_json_file, 'r') as f:
            original_data = json.load(f)
        
        # Check if word_segments exists
        if "word_segments" not in original_data:
            raise KeyError("Key 'word_segments' not found in JSON data.")
        
        # Return the original data - no transformation needed
        return original_data
    
    except Exception as e:
        logging.error(f"Error loading JSON file: {e}")
        raise


def get_start_end_timestamps(philtered_json):
    """
    Extract start and end timestamps from JSON data.
    
    Parameters:
        philtered_json (dict): JSON data containing word_segments.
    
    Returns:
        list: List of dictionaries containing valid start and end timestamps.
    
    Raises:
        KeyError: If word_segments is not found.
    """
    try:
        # Check if "word_segments" exists
        if "word_segments" not in philtered_json:
            raise KeyError("Key 'word_segments' not found in JSON data.")
        
        word_segments = philtered_json["word_segments"]
        valid_intervals = []
        
        # Process each word segment
        for _, segment_data in word_segments.items():
            word = segment_data.get('word', '')
            
            # Check if word contains PHI pattern
            if re.search(PHI_PATTERN, word):
                try:
                    start = float(segment_data.get('start', 0))
                    end = float(segment_data.get('end', 0))
                    
                    # Validate interval
                    if start < end:
                        interval = {
                            'start': start,
                            'end': end,
                            'word': word
                        }
                        valid_intervals.append(interval)
                        logging.debug('Added PHI interval: word="%s", start=%s, end=%s', 
                                    word, start, end)
                    else:
                        logging.warning('Invalid interval for word "%s": start=%s >= end=%s', 
                                      word, start, end)
                except (ValueError, TypeError) as e:
                    logging.warning('Failed to parse timestamps for word "%s": %s', word, e)
        
        # Sort intervals by start time and check for overlaps
        valid_intervals.sort(key=lambda x: x['start'])
        
        # Check for overlapping intervals
        for i in range(1, len(valid_intervals)):
            if valid_intervals[i]['start'] < valid_intervals[i-1]['end']:
                logging.warning('Overlapping intervals detected: [%s-%s] and [%s-%s]',
                              valid_intervals[i-1]['start'], valid_intervals[i-1]['end'],
                              valid_intervals[i]['start'], valid_intervals[i]['end'])
        
        logging.info('Found %d valid PHI intervals to scrub', len(valid_intervals))
        return valid_intervals
    
    except Exception as e:
        logging.error('Error occurred while processing JSON data: %s', e)
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
        RuntimeError: If video has no audio track.
    """
    # Use system temp directory for temporary files
    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_audio:
        temp_audio_file = temp_audio.name
    
    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_scrubbed:
        temp_scrubbed_audio_file = temp_scrubbed.name
    
    try:
        # Check if the source is a video
        is_video = source_path.lower().endswith(SUPPORTED_VIDEO_FORMATS)
        audio = None
        
        # Load audio from video or audio file
        if is_video:
            with VideoFileClip(source_path) as video:
                if video.audio is None:
                    raise RuntimeError(f"Video file '{source_path}' has no audio track.")
                video.audio.write_audiofile(temp_audio_file, codec="mp3", verbose=False, logger=None)
                audio = AudioSegment.from_file(temp_audio_file)
                logging.info('Loaded video and extracted audio.')
        else:
            audio = AudioSegment.from_file(source_path)
            logging.info('Loaded audio file.')
        
        # Check if beep file exists
        beep_path = os.path.join(os.path.dirname(__file__), "beep.mp3")
        if not os.path.isfile(beep_path):
            raise FileNotFoundError(f"Beep file 'beep.mp3' not found at {beep_path}")
        
        # Load the beep sound
        beep = AudioSegment.from_file(beep_path)
        
        # Use empty AudioSegment and concatenate (more memory efficient)
        scrubbed_audio = AudioSegment.empty()
        last_end_time = 0
        
        for i, interval in enumerate(time_intervals):
            # Convert start and end times to milliseconds
            start_time = int(interval['start'] * MS_PER_SECOND)
            end_time = int(interval['end'] * MS_PER_SECOND)
            
            # Sanitize PHI word for logging
            sanitized_word = re.sub(r'\*\*(\w+)\*\*', r'**[REDACTED]**', interval.get('word', 'N/A'))
            
            logging.info(
                'Processing interval %d/%d: [%.3fs-%.3fs], PHI type=%s', 
                i + 1, len(time_intervals), interval['start'], interval['end'], 
                sanitized_word)
            
            # Add the audio segment before the interval
            if start_time > last_end_time:
                scrubbed_audio += audio[last_end_time:start_time]
            
            interval_duration = end_time - start_time
            
            # Create beep segment of appropriate length
            if beep.duration_seconds * MS_PER_SECOND < interval_duration:
                loops = (interval_duration // int(beep.duration_seconds * MS_PER_SECOND)) + 1
                beep_segment = beep * loops
                beep_segment = beep_segment[:interval_duration]
            else:
                beep_segment = beep[:interval_duration]
            
            scrubbed_audio += beep_segment
            last_end_time = end_time
        
        # Add the remaining audio after the last interval
        if last_end_time < len(audio):
            scrubbed_audio += audio[last_end_time:]
        
        # Export scrubbed audio to temporary file
        scrubbed_audio.export(temp_scrubbed_audio_file, format="mp3")
        
        # If a target video path is provided, reattach the scrubbed audio to it
        if target_video_path:
            with VideoFileClip(target_video_path) as target_video:
                # Use context manager for AudioFileClip to prevent resource leak
                with AudioFileClip(temp_scrubbed_audio_file) as scrubbed_audio_clip:
                    final_video = target_video.set_audio(scrubbed_audio_clip)
                    
                    # Check that output path has a video-compatible extension
                    if not scrubbed_audio_path.lower().endswith(SUPPORTED_VIDEO_FORMATS):
                        raise ValueError(
                            f"Output path should have a video-compatible extension "
                            f"like {', '.join(SUPPORTED_VIDEO_FORMATS)}")
                    
                    # Write the final video with audio
                    final_video.write_videofile(
                        scrubbed_audio_path, codec="libx264", audio_codec="aac",
                        verbose=False, logger=None
                    )
            logging.info('Saved scrubbed video with reattached audio to %s', scrubbed_audio_path)
        else:
            # If no target video path, save scrubbed audio directly
            scrubbed_audio.export(scrubbed_audio_path, format="mp3")
            logging.info('Saved scrubbed audio to %s', scrubbed_audio_path)
    
    except Exception as e:
        logging.error('Error occurred while scrubbing audio: %s', e)
        raise
    finally:
        # Clean up temporary files
        for temp_file in [temp_audio_file, temp_scrubbed_audio_file]:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                    logging.debug('Removed temporary file: %s', temp_file)
                except OSError as e:
                    logging.warning('Failed to remove temporary file %s: %s', temp_file, e)


def main():
    parser = argparse.ArgumentParser(
        description='Scrub audio from an audio or video file and replace PHI segments with beeps.')
    parser.add_argument('--source', required=True,
                        help='Path to the source audio or video file.')
    parser.add_argument('--json', required=True,
                        help='Path to the JSON file containing PHI time intervals.')
    parser.add_argument('--output', required=True,
                        help='Path to the scrubbed audio or video file.')
    parser.add_argument(
        '--target_video', help='Path to a different video file to reattach the scrubbed audio.')
    parser.add_argument('--log', action='store_true', help='Enable detailed logging.')
    
    args = parser.parse_args()
    
    # Configure logging
    if args.log:
        # Create logs directory if it doesn't exist
        logs_dir = os.path.join(os.path.dirname(__file__), 'logs')
        os.makedirs(logs_dir, exist_ok=True)
        
        log_filename = os.path.join(logs_dir, f"log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        logging.basicConfig(filename=log_filename, level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s')
        logging.info('Starting audio scrubbing process')
    else:
        # Set up basic logging to avoid errors when logging is called
        logging.basicConfig(level=logging.WARNING,
                            format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Validate paths
    if not os.path.isfile(args.source):
        raise FileNotFoundError(f"Source file '{args.source}' not found.")
    if not os.path.isfile(args.json):
        raise FileNotFoundError(f"JSON file '{args.json}' not found.")
    if args.target_video and not os.path.isfile(args.target_video):
        raise FileNotFoundError(f"Target video file '{args.target_video}' not found.")
    
    try:
        # Load and process JSON data
        json_data = transform_json_schema(args.json)
        
        # Get the start and end timestamps from the JSON file
        filtered_intervals = get_start_end_timestamps(json_data)
        
        if not filtered_intervals:
            logging.warning('No PHI intervals found in the JSON file.')
            print("Warning: No PHI intervals found in the JSON file.")
        else:
            # Log summary without exposing PHI
            logging.info('Processing %d PHI intervals', len(filtered_intervals))
            
            # Scrub the audio and write to file
            scrub_audio(args.source, filtered_intervals, args.output, args.target_video)
            logging.info('Audio scrub completed successfully.')
            print(f"Audio scrubbing completed. Output saved to: {args.output}")
    
    except Exception as e:
        logging.error('Failed to complete audio scrubbing: %s', e)
        print(f"Error: {e}")
        raise


if __name__ == "__main__":
    main()