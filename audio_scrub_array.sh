#!/bin/bash
#SBATCH --job-name=audio_deid_array                              # Job name
#SBATCH --output=audio_deid_%A_%a.out                            # Output file name (%A is the job array ID, %a is the task index)
#SBATCH --error=audio_deid_%A_%a.err                             # Error file name
#SBATCH --mail-user=your@email.com                               # Email notifications
#SBATCH --mail-type=END,FAIL                                     # Notify on job completion or failure
#SBATCH --ntasks=1                                               # Number of tasks per array job
#SBATCH --cpus-per-task=32                                       # Number of CPU cores
#SBATCH --mem-per-cpu=2G                                         # Memory per core
#SBATCH --time=04:00:00                                          # Maximum runtime
#SBATCH --array=0-18                                             # Create a job array with 19 jobs (adjust the size based on the number of videos)

# Load the required modules
module load python/3.11

# Activate the virtual environment
source /path/to/venv/bin/activate

# Define base paths for convenience
BASE_VIDEO_PATH="/base/path/to/videos"
BASE_JSON_PATH="/base/path/to/json"
OUTPUT_BASE_PATH="/output/path"
TARGET_VIDEO_BASE_PATH="/target/video/path"
PYTHON_SCRIPT_PATH="/python/script/path"

# List of video files to process
original_videos=(
    "file.mp4"
    "file.mp4"
    "file.mp4"
    "file.mp4"
    "file.mp4"
    "file.mp4"
    "file.mp4"
    "file.mp4"
    "file.mp4"
    "file.mp4"
    "file.mp4"
    "file.mp4"
    "file.mp4"
    "file.mp4"
    "file.mp4"
    "file.mp4"
    "file.mp4"
    "file.mp4"
    "file.mp4"
)

# Select the video file based on SLURM_ARRAY_TASK_ID
ORIGINAL_VIDEO_PATH="$BASE_VIDEO_PATH/${original_videos[$SLURM_ARRAY_TASK_ID]}"
JSON_TRANSCRIPT_PATH="$BASE_JSON_PATH/$(basename ${ORIGINAL_VIDEO_PATH%.MP4}-philtered.json)"
OUTPUT_PATH="$OUTPUT_BASE_PATH/$(basename ${ORIGINAL_VIDEO_PATH%.MP4}_complete_deid.mp4)"
TARGET_VIDEO_PATH="$TARGET_VIDEO_BASE_PATH/$(basename ${ORIGINAL_VIDEO_PATH%.MP4}_deid.mp4)"

python "$PYTHON_SCRIPT_PATH" --source "$ORIGINAL_VIDEO_PATH" --json "$JSON_TRANSCRIPT_PATH" --output "$OUTPUT_PATH" --target_video "$TARGET_VIDEO_PATH" --log
