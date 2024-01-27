import os
import glob
import subprocess
from moviepy.editor import VideoFileClip
import whisper
import datetime
from googletrans import Translator
import time
from tqdm import tqdm
import json

# Load the Whisper model
model = whisper.load_model("base")

# Function to extract audio from a video file


def extract_audio(video_file):
    with VideoFileClip(video_file) as video:
        audio_file = f"{os.path.splitext(video_file)[0]}.wav"
        video.audio.write_audiofile(audio_file, codec='pcm_s16le')
    return audio_file


# Function for translation to Chinese
translator = Translator()


def translate_text(text, dest_language):
    return translator.translate(text, dest=dest_language).text

# Function to transcribe audio and generate SRT subtitles


def transcribe_to_srt(audio_file):
    print(f"Starting transcription for {audio_file}")
    result = model.transcribe(audio_file)
    print(f"Transcription completed for {audio_file}")

    srt_filename = f"{os.path.splitext(audio_file)[0]}.srt"
    print(f"Creating SRT file {srt_filename}")

    with open(srt_filename, "w") as f:
        for i, segment in enumerate(result["segments"]):
            start_time = datetime.timedelta(seconds=segment['start'])
            end_time = datetime.timedelta(seconds=segment['end'])

            f.write(f"{i+1}\n")
            f.write(
                f"{str(start_time).split('.')[0]} --> {str(end_time).split('.')[0]}\n")
            f.write(f"{segment['text']}\n\n")

    print(f"SRT file created for {audio_file}")

    os.remove(audio_file)  # Clean up audio file after processing
    print(f"Audio file removed for {audio_file}")

    return srt_filename



# Function to transcribe + translate


def transcribe_and_translate_to_srt(audio_file, dest_language='zh-TW'):
    print(f"Starting transcription for {audio_file}")
    result = model.transcribe(audio_file, verbose=True)
    print(f"Transcription completed for {audio_file}")

    # Serialize the result to a JSON file
    intermediate_file = f"{os.path.splitext(audio_file)[0]}_transcription.json"
    with open(intermediate_file, "w", encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False)

    srt_filename = f"{os.path.splitext(audio_file)[0]}.srt"
    print(f"Creating SRT file {srt_filename}")

    # Read from the intermediate file
    with open(intermediate_file, "r", encoding='utf-8') as f:
        result = json.load(f)

    with open(srt_filename, "wb") as f:
        for i, segment in enumerate(tqdm(result["segments"], desc="Transcribing and translating")):
            start_time_segment = datetime.timedelta(seconds=segment['start'])
            end_time_segment = datetime.timedelta(seconds=segment['end'])
            original_text = segment['text']
            translated_text = None
            attempts = 0
            while translated_text is None and attempts < 10:
                try:
                    translated_text = translate_text(original_text, dest_language)
                except Exception as e:
                    print(f"An error occurred during translation: {e}, will try again")
                    attempts += 1
                    time.sleep(1)  # Adjust the delay as necessary
            if translated_text is None:
                print(f"Failed to translate segment {i} after 10 attempts.")
                continue
            f.write((f"{i+1}\n").encode('utf-8'))
            f.write((f"{str(start_time_segment).split('.')[0]} --> {str(end_time_segment).split('.')[0]}\n").encode('utf-8'))
            f.write((f"{translated_text}\n\n").encode('utf-8'))

    print(f"SRT file created and translated for {audio_file}")

    # Delete the intermediate file
    #os.remove(intermediate_file)
    #print(f"Intermediate file removed for {audio_file}")

    return srt_filename



# Function to add subtitles to a video


def add_subtitles_to_video(video_file, srt_file):
    output_file = f"{os.path.splitext(video_file)[0]}-c.mp4"
    print(f"Adding subtitles to {video_file} and saving as {output_file}")
    with open(srt_file, 'r') as f:
        print(f"Contents of {srt_file}:\n{f.read()}")
    video_file_abs = os.path.abspath(video_file)
    subprocess.run(["ffmpeg", "-i", f'"{video_file_abs}"',
                   "-vf", f'subtitles="{srt_file}"', f'"{output_file}"'])
    print(f"Finished adding subtitles to {video_file}")


# Process all video files in the current directory
def main():
    # Example of processing all video files
    for video_file in glob.glob("*.mp4") + glob.glob("*.wmv"):
        audio_file = extract_audio(video_file)
        srt_file = transcribe_and_translate_to_srt(audio_file)
        # If you want to add subtitles directly uncomment the next line
        # add_subtitles_to_video(video_file, srt_file)

if __name__ == "__main__":
    main()


# Optional: Add SRT subtitles to the video files (requires ffmpeg)
# for video_file in glob.glob("*.mp4"):
#     srt_file = f"{os.path.splitext(video_file)[0]}.srt"
#     output_file = f"{os.path.splitext(video_file)[0]}_subtitled.mp4"
#     subprocess.run(["ffmpeg", "-i", video_file, "-vf", f"subtitles={srt_file}", output_file])
