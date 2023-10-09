import json
import sys
import pandas as pd
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_audioclips

def get_start_end_timestamps(philtered_json):
    """
    Extract start and end timestamps from a JSON file.
    
    Parameters:
        philtered_json (str): Path to the JSON file containing word segments.
        
    Returns:
        str: A JSON string containing start and end timestamps of filtered word segments.
    """
    with open(philtered_json, "r") as f:
        json_data = json.load(f)
    
    # Convert JSON data to DataFrame for easier manipulation
    word_segments_df = pd.DataFrame(json_data["word_segments"].values())
    
    # Regular expression pattern to identify words enclosed with double asterisks
    pattern = r'\*\*(\w+)\*\*'
    
    # Filter rows that contain the pattern
    filtered_df = word_segments_df[word_segments_df['word'].str.contains(
        pattern, regex=True)]
    
    # Convert filtered data to JSON format
    filtered_json = filtered_df[['start', 'end']].to_json(orient='records')
    
    return filtered_json

def scrub_audio(source_video_path, beep_path, time_intervals, scrubbed_video_path):
    """
    Scrub audio from a video file and insert beep sounds at specified intervals.
    
    Parameters:
        source_video_path (str): Path to the original video file.
        beep_path (str): Path to the beep sound file.
        time_intervals (list): List of dictionaries containing start and end times for beeps.
        scrubbed_video_path (str): Path to save the modified video file.
    """
    # Load video and extract its audio
    video = VideoFileClip(source_video_path)
    original_audio = video.audio
    
    # Load the beep sound to be inserted
    beep = AudioFileClip(beep_path)
    
    # Initialize a list to store segments of the audio track
    audio_segments = []
    last_end_time = 0
    
    # Iterate through each interval, replacing original audio with beep sound
    for interval in time_intervals:
        start_time = float(interval['start'])
        end_time = float(interval['end'])
        
        # Append original audio segment before the beep
        audio_segments.append(original_audio.subclip(last_end_time, start_time))
        
        # Ensure beep sound fits into the specified interval
        beep_duration = beep.duration  
        interval_duration = end_time - start_time  
        
        # Check if beep sound needs to be looped or trimmed to fit the interval
        if beep_duration < interval_duration:
            loops = int(interval_duration // beep_duration) + 1  
            beep_to_add = concatenate_audioclips([beep] * loops)  
            beep_to_add = beep_to_add.subclip(0, interval_duration)
        else:
            beep_to_add = beep.subclip(0, interval_duration)
        
        # Append the beep sound
        audio_segments.append(beep_to_add)
        last_end_time = end_time
    
    # Append remaining original audio after the last beep
    audio_segments.append(original_audio.subclip(last_end_time, original_audio.duration))
    
    # Concatenate all audio segments and set the modified audio to the original video
    modified_audio = concatenate_audioclips(audio_segments)
    video_with_beep = video.set_audio(modified_audio)
    
    # Export the modified video with the new audio track
    video_with_beep.write_videofile(scrubbed_video_path, codec="libx264", audio_codec="aac")
    
    # Close objects to free resources
    video.close()
    original_audio.close()
    modified_audio.close()

def seconds_to_minutes(time_data):
    """
    Convert time data from seconds to minutes.
    
    Parameters:
        time_data (list): List of dictionaries containing start and end times in seconds.
        
    Returns:
        list: Updated time data with start and end times in minutes.
    """
    # Convert each start and end time from seconds to minutes
    for entry in time_data:
        entry['start'] = float(entry['start']) / 60
        entry['end'] = float(entry['end']) / 60
    return time_data

def main():
    """
    Main function to execute the script.
    Retrieves command line arguments, extracts and prints timestamps, and scrubs audio.
    """
    # Retrieve file paths and JSON data from command line arguments
    video_file_path = sys.argv[1]
    beep_file_path = sys.argv[2]
    start_stop_timestamps_json = sys.argv[3]
    scrubbed_video_file_path = sys.argv[4]

    # Perform the audio scrubbing operation
    scrub_audio(video_file_path, beep_file_path, json.loads(get_start_end_timestamps(start_stop_timestamps_json)), scrubbed_video_file_path)

if __name__ == "__main__":
    """
    Check if the script is run directly and if the correct number of command line arguments are provided.
    If conditions are met, run the main function.
    """
    # Ensure the correct number of arguments are provided
    num_args = len(sys.argv) - 1
    if num_args != 4:
        print("Usage: python scrub.py <video_file_path> <beep_file_path> <start_stop_timestamps_json> <scrubbed_video_file_path>")
        sys.exit(1)
    
    # Execute the main function
    main()
    sys.exit(0)
