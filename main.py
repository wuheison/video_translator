import os
import glob
import subprocess
from moviepy.editor import VideoFileClip
import whisper
import datetime

# Load the Whisper model
model = whisper.load_model("base")

# Function to extract audio from a video file


def extract_audio(video_file):
    with VideoFileClip(video_file) as video:
        audio_file = f"{os.path.splitext(video_file)[0]}.wav"
        video.audio.write_audiofile(audio_file, codec='pcm_s16le')
    return audio_file

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
for video_file in glob.glob("*.mp4"):
    audio_file = extract_audio(video_file)
    srt_file = transcribe_to_srt(audio_file)
    # Error in opening video
    # add_subtitles_to_video(video_file, srt_file)


# Optional: Add SRT subtitles to the video files (requires ffmpeg)
# for video_file in glob.glob("*.mp4"):
#     srt_file = f"{os.path.splitext(video_file)[0]}.srt"
#     output_file = f"{os.path.splitext(video_file)[0]}_subtitled.mp4"
#     subprocess.run(["ffmpeg", "-i", video_file, "-vf", f"subtitles={srt_file}", output_file])
