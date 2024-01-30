#!/bin/bash

# Directory containing the JSON files
JSON_DIR="/path/to/json/files"

# Source video directory path
SOURCE_VIDEOS_DIR="/path/to/source/videos"

# Output directory for the scrubbed audio files
OUTPUT_DIR="/path/to/output/directory"

# Log file
LOG_FILE="$OUTPUT_DIR/audio_pipeline.log"

# Name of the Anaconda environment
ENV_NAME="scrub"

# Enable logging
log=false

# Exit immediately if a command exits with a non-zero status
set -e

# Get the current directory
CURRENT_DIR=$(pwd)

# Path to the requirements file
REQUIREMENTS_FILE="$CURRENT_DIR/requirements.txt"

# Check if the Anaconda environment exists, if not, create it
if [[ $(conda env list | awk '{print $1}' | grep -w "$ENV_NAME") != "$ENV_NAME" ]]; then
    echo "Creating Anaconda environment $ENV_NAME"
    conda create -n "$ENV_NAME" -y
fi

# Activate the Anaconda environment
source ~/anaconda3/etc/profile.d/conda.sh
conda activate "$ENV_NAME"

# Install the Python packages from the requirements file
echo "Installing Python packages from $REQUIREMENTS_FILE"
pip install -r "$REQUIREMENTS_FILE"

# Create the output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Start logging
exec > >(tee -a "$LOG_FILE") 2>&1

# Remove spaces from the video file names
find "$SOURCE_VIDEOS_DIR" -type f -name "* *" -print0 | while IFS= read -r -d '' file; do
    mv "$file" "${file// /_}"
done

# Iterate over the JSON files in the directory
for json_file in "$JSON_DIR"/*.json; do
    # Get the base name of the JSON file to use for the output file name
    base_name=$(basename "$json_file" -philtered.json)

    # Find the corresponding video file
    video_file=$(find "$SOURCE_VIDEOS_DIR" -type f -name "$base_name.*")

    # If a matching video file was not found, skip this iteration
    if [ -z "$video_file" ]; then
        echo "No matching video file found for $json_file"
        continue
    fi

    # Construct the output file path
    output_audio_path="$OUTPUT_DIR/$base_name.mp3"

    # Run the Python script
    if [ "$log" = true ]; then
        python scrub.py --source "$video_file" --json "$json_file" --output "$output_audio_path" --log
    else
        python scrub.py --source "$video_file" --json "$json_file" --output "$output_audio_path"
    fi
done
