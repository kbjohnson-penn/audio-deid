import argparse
import json
import logging
from datetime import datetime
import pandas as pd
from pydub import AudioSegment


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


def scrub_audio(source_audio_path, time_intervals, scrubbed_audio_path):
    """
    Scrub audio from a video file and replace with beeps.

    Parameters:
        source_audio_path (str): Path to the source audio file.
        time_intervals (list): List of dictionaries containing start and end times in milliseconds.
        scrubbed_audio_path (str): Path to the scrubbed audio file.
    """
    try:
        audio = AudioSegment.from_file(source_audio_path)
        beep = AudioSegment.from_file("beep.mp3")

        logging.info('Loaded audio file')

        segments = []
        last_end_time = 0

        for interval in time_intervals:
            # Convert to milliseconds
            start_time = int(float(interval['start']) * 1000)
            # Convert to milliseconds
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

            logging.info('Processed interval from %s to %s',
                         start_time, end_time)

        # Add the audio segment after the last interval
        segments.append(audio[last_end_time:])

        scrubbed_audio = sum(segments)
        scrubbed_audio.export(scrubbed_audio_path, format="mp3")

        logging.info('Saved scrubbed audio to %s', scrubbed_audio_path)

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
                        help='Path to the source audio file.')
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

    # Get the start and end timestamps from the JSON file
    filtered_json = get_start_end_timestamps(args.json)
    logging.info('Filtered JSON: %s', filtered_json)

    # Scrub the audio and write to file
    scrub_audio(args.source, filtered_json, args.output)
    logging.info('Audio scrub completed.')


if __name__ == "__main__":
    main()
