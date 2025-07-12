"""
Audio transcription using WhisperX for audio de-identification pipeline.
"""

import argparse
import os
import logging
from pathlib import Path


def transcribe(audio_path, model_size, language, temperature, device, output_format, output_dir, batch_size=16, compute_type="float16"):
    """
    Transcribe a audio file with WhisperX and write result to file.
    (WhisperX: https://github.com/m-bain/whisperX/tree/main)

    args:
        audio_path (str): Path to audio file
        model_size (str): Whisper model to use
        language (str): Language to transcribe to
        temperature (float): Temperature for sampling
        device (str) : Device to use
        output_format (str): Whisper output format (e.g., tsv, json)
        output_dir (str): Path to output file
        batch_size (int) : Batch size for inference, defaults to 16
        compute_type (str) : Compute type for inference, defaults to float16

    return:
        str: Path to transcript file if successful, None if failed
    """
    try:
        import whisperx
    except ImportError:
        print("ERROR: WhisperX not installed. Install with: pip install whisperx")
        return None
    
    # Validate audio path
    audio_path = Path(audio_path).resolve()
    if not audio_path.exists():
        print(f"ERROR: Audio file not found: {audio_path}")
        return None
    
    try:
        # Load Whisper model
        model = whisperx.load_model(model_size, device, compute_type=compute_type)

        # Load the audio
        audio = whisperx.load_audio(str(audio_path))

        # Transcribe
        result = model.transcribe(audio, batch_size=batch_size, language=language)

        # Align timestamps
        model_a, metadata = whisperx.load_align_model(language_code=result["language"], device=device)
        result = whisperx.align(result["segments"], model_a, metadata, audio, device, return_char_alignments=False)

        # Save the result
        if output_dir is None:
            output_dir = str(audio_path.parent)
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        results_writer = whisperx.utils.get_writer(output_format, str(output_dir))
        results_writer(result, str(audio_path), {})
        
        # Return path to transcript file
        transcript_path = output_dir / f"{audio_path.stem}.{output_format}"
        if transcript_path.exists():
            return str(transcript_path)
        else:
            # Try alternative naming convention
            transcript_path = output_dir / f"transcript.{output_format}"
            if transcript_path.exists():
                return str(transcript_path)
        
        return None
        
    except Exception as e:
        print(f"ERROR: Transcription failed: {e}")
        return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--audio", type=str, help="Audio file path", required=True)
    parser.add_argument("--model_size", type=str, help="Whisper model. Defaults to \"turbo\".", default="turbo")
    parser.add_argument("--language", type=str, help="Audio language. Defaults to English (\"en\").", default="en")
    parser.add_argument("--temperature", type=float, help="Temperature for scaling. Defaults to 0.0.", default=0.0)
    parser.add_argument("--device", type=str, help="Device. Defaults to \"cuda\".", default="cuda")
    parser.add_argument("--output_format", type=str, help="Whisper output format. Defaults to \"json\".", default="json")
    parser.add_argument("--output_dir", type=str, help="Output directory. Defaults to the same directory as the input audio.", default=None)

    args = parser.parse_args()

    result = transcribe(args.audio, args.model_size, args.language, args.temperature, args.device, args.output_format, args.output_dir)
    
    if result:
        print(f"SUCCESS: Transcript saved to {result}")
    else:
        print("FAILED: Transcription failed")