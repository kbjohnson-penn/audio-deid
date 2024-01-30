import argparse
import json
import logging
from datetime import datetime
import pandas as pd
import warnings
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_audioclips

# Ignore warnings related to regex pattern
warnings.filterwarnings("ignore", 'This pattern is interpreted as a regular expression')

# Regular expression pattern to identify words enclosed with double asterisks
pattern = r'\*\*(\w+)\*\*'


def get_start_end_timestamps(philtered_json):
    """
    Extract start and end timestamps from a JSON file.

    Parameters:
        philtered_json (str): Path to the JSON file containing word segments.

    Returns:
        list: List of dictionaries containing start and end timestamps.
    """
    try:
        logging.info(
            'Loading JSON data from %s and converting to Dataframe', philtered_json)

        # Load JSON data from file
        with open(philtered_json, "r") as f:
            json_data = json.load(f)

        # Convert JSON data to DataFrame for easier manipulation
        word_segments_df = pd.DataFrame(json_data["word_segments"].values())

        # Filter rows that contain the pattern
        filtered_df = word_segments_df[word_segments_df['word'].str.contains(
            pattern, regex=True, na=False)]

        # Convert filtered data to list of dictionaries
        filtered_json = filtered_df[['start', 'end']].to_dict(orient='records')

        logging.info('Converted filtered data to list of dictionaries')

        return filtered_json

    except Exception as e:
        logging.error('Error occurred while loading JSON data: %s', e)
        raise


def scrub_audio(source_video_path, time_intervals, scrubbed_audio_path):
    """
    Scrub audio from a video file and replace with beeps.

    Parameters:
        source_video_path (str): Path to the source video file.
        time_intervals (list): List of dictionaries containing start and end times in minutes.
        scrubbed_audio_path (str): Path to the scrubbed audio file.

    Returns:
        None
    """

    try:
        # Load the video and audio files
        video = VideoFileClip(source_video_path)
        original_audio = video.audio
        beep = AudioFileClip("beep.mp3")

        logging.info('Loaded video and audio files')

        audio_segments = []
        last_end_time = 0

        # Iterate through each time interval and replace with beeps
        for interval in time_intervals:
            start_time = float(interval['start'])
            end_time = float(interval['end'])

            # Calculate the duration of the interval
            interval_duration = end_time - start_time

            # Add the audio segment before the interval
            audio_segments.append(
                original_audio.subclip(last_end_time, start_time))

            beep_duration = beep.duration

            # Check if the beep needs to be repeated
            if beep_duration < interval_duration:
                # Calculate the number of times the beep needs to be repeated
                loops = int(interval_duration // beep_duration) + 1
                beep_to_add = concatenate_audioclips([beep] * loops)
                beep_to_add = beep_to_add.subclip(0, interval_duration)
            else:
                # Trim the beep to the duration of the interval
                beep_to_add = beep.subclip(0, interval_duration)

            # Add the beep to the audio segments
            audio_segments.append(beep_to_add)
            last_end_time = end_time

            logging.info('Processed interval from %s to %s',
                         start_time, end_time)

        # Add the audio segment after the last interval
        audio_segments.append(original_audio.subclip(
            last_end_time, original_audio.duration))

        # Concatenate all audio segments and write to file
        modified_audio = concatenate_audioclips(audio_segments)
        modified_audio.write_audiofile(scrubbed_audio_path)

        logging.info('Saved scrubbed audio to %s', scrubbed_audio_path)

        # Close all files
        video.close()
        original_audio.close()
        modified_audio.close()

    except Exception as e:
        logging.error('Error occurred while scrubbing audio: %s', e)
        raise


def main():
    """
    Parse command line arguments and run the scrub_audio function.

    Parameters:
        None

    Returns:
        None
    """

    parser = argparse.ArgumentParser(
        description='Scrub audio from a video file and replace with beeps.')
    parser.add_argument('--source', required=True,
                        help='Path to the source video file.')
    parser.add_argument('--json', required=True,
                        help='Path to the JSON file containing time intervals.')
    parser.add_argument('--output', required=True,
                        help='Path to the scrubbed audio file.')
    parser.add_argument('--log', action='store_true', help='Enable logging.')

    args = parser.parse_args()

    # Set up logging if --log argument is passed
    if args.log:
        log_filename = f"log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        logging.basicConfig(filename=log_filename, level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s')

    # Get the start and end timestamps from the JSON file
    filtered_json = get_start_end_timestamps(args.json)

    # Scrub the audio and write to file
    scrub_audio(args.source, filtered_json, args.output)

    logging.info('Audio scrub completed.')


if __name__ == "__main__":
    """
    Run the main function.

    Parameters:
        None

    Returns:
        None
    """

    main()
