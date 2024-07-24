import argparse
import json
import logging
from datetime import datetime
import pandas as pd
import warnings
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_audioclips

# Ignore warnings related to regex pattern
warnings.filterwarnings(
    "ignore", 'This pattern is interpreted as a regular expression')

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


def scrub_audio(source_video_path, time_intervals, scrubbed_audio_path):
    """
    Scrub audio from a video file and replace with beeps.

    Parameters:
        source_video_path (str): Path to the source video file.
        time_intervals (list): List of dictionaries containing start and end times in minutes.
        scrubbed_audio_path (str): Path to the scrubbed audio file.
    """
    try:
        video = VideoFileClip(source_video_path)
        original_audio = video.audio
        beep = AudioFileClip("beep.mp3")

        logging.info('Loaded video and audio files')

        audio_segments = []
        last_end_time = 0

        for interval in time_intervals:
            start_time = float(interval['start'])
            end_time = float(interval['end'])

            logging.info(
                'Processing interval: start_time=%s, end_time=%s', start_time, end_time)

            interval_duration = end_time - start_time

            if last_end_time < start_time:
                audio_segment = original_audio.subclip(
                    last_end_time, start_time)
                logging.info(
                    'Audio segment duration before interval: %s', audio_segment.duration)
                audio_segments.append(audio_segment)

            beep_duration = beep.duration

            if beep_duration < interval_duration:
                loops = int(interval_duration // beep_duration) + 1
                beep_to_add = concatenate_audioclips(
                    [beep] * loops).subclip(0, interval_duration)
            else:
                beep_to_add = beep.subclip(0, interval_duration)

            logging.info('Beep segment duration: %s', beep_to_add.duration)
            audio_segments.append(beep_to_add)
            last_end_time = end_time

            logging.info('Processed interval from %s to %s',
                         start_time, end_time)

        if last_end_time < original_audio.duration:
            audio_segment = original_audio.subclip(
                last_end_time, original_audio.duration)
            logging.info(
                'Audio segment duration after last interval: %s', audio_segment.duration)
            audio_segments.append(audio_segment)

        modified_audio = concatenate_audioclips(audio_segments)

        logging.info('Modified audio duration: %s', modified_audio.duration)

        if modified_audio.duration != modified_audio.duration:  # NaN check
            raise ValueError(
                "Modified audio duration is NaN. Please check the source file and intervals.")

        modified_audio.write_audiofile(scrubbed_audio_path)

        logging.info('Saved scrubbed audio to %s', scrubbed_audio_path)

        video.close()
        original_audio.close()
        modified_audio.close()

    except Exception as e:
        logging.error('Error occurred while scrubbing audio: %s', e)
        raise


def main():
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

    if args.log:
        log_filename = f"log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        logging.basicConfig(filename=log_filename, level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s')

    filtered_json = get_start_end_timestamps(args.json)
    logging.info('Filtered JSON: %s', filtered_json)

    scrub_audio(args.source, filtered_json, args.output)
    logging.info('Audio scrub completed.')


if __name__ == "__main__":
    main()
