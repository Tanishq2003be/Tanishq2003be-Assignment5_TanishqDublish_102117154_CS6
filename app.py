import streamlit as st
import re
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from googleapiclient.discovery import build
from moviepy.audio.io.AudioFileClip import AudioFileClip
from pytube import YouTube
from moviepy.editor import VideoFileClip, concatenate_audioclips


def get_youtube_service(api_key):
    return build('youtube', 'v3', developerKey=api_key)


def get_video_id(url):
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", url)
    return match.group(1) if match else None


def download_videos(api_key, singer_name, num_videos):
    st.write(
        f"Downloading {num_videos} videos of {singer_name} from YouTube using API...")
    youtube_service = get_youtube_service(api_key)
    query = f"{singer_name} songs"

    # Search for videos using the YouTube Data API
    search_response = youtube_service.search().list(
        q=query,
        type='video',
        part='id',
        maxResults=num_videos
    ).execute()

    video_ids = [item['id']['videoId'] for item in search_response['items']]

    for i, video_id in enumerate(video_ids):
        try:
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            st.write(f"Downloading Video {i + 1} - ID: {video_id}")
            YouTube(video_url).streams.get_highest_resolution().download()
        except Exception as e:
            st.error(f"Error downloading Video {i + 1}: {e}")


def convert_to_audio():
    st.write("Converting videos to audio...")
    for file in os.listdir():
        if file.endswith(".mp4"):
            video = VideoFileClip(file)
            audio = video.audio
            audio.write_audiofile(file.replace(".mp4", ".mp3"))
            video.close()
            audio.close()


def cut_audio(duration):
    st.write(f"Cutting first {duration} seconds from all downloaded audios...")
    for file in os.listdir():
        if file.endswith(".mp3"):
            audio = AudioFileClip(file)
            audio = audio.subclip(0, duration)
            audio.write_audiofile(file)
            audio.close()


def merge_audios(output_filename):
    st.write("Merging all audios into a single output file...")
    audio_clips = [AudioFileClip(file)
                   for file in os.listdir() if file.endswith(".mp3")]
    final_audio = concatenate_audioclips(audio_clips)
    final_audio.write_audiofile(output_filename)


def send_email(email_address, output_filename):
    try:
        # Create message container
        msg = MIMEMultipart()
        msg['From'] = "your-email@example.com"
        msg['To'] = email_address
        msg['Subject'] = "YouTube Mashup Information"

        # Add body to email
        body = f"Your mashup is ready! You can download it from the following link: {output_filename}"
        msg.attach(MIMEText(body, 'plain'))

        # Connect to SMTP server
        server = smtplib.SMTP('smtp.example.com', 587)
        server.starttls()
        server.login("your-email@example.com", "your-password")

        # Send email
        server.sendmail("your-email@example.com",
                        email_address, msg.as_string())
        server.quit()

        st.success("Email sent successfully!")
    except Exception as e:
        st.error(f"Error sending email: {e}")


def mashup(api_key, singer_name, num_videos, audio_duration, output_filename, email_address):
    try:
        download_videos(api_key, singer_name, num_videos)
        convert_to_audio()
        cut_audio(audio_duration)
        merge_audios(output_filename)
        send_email(email_address, output_filename)
        st.success(f"Mashup completed! Output file: {output_filename}")
    except Exception as e:
        st.error(f"Error: {e}")


if __name__ == "__main__":
    st.title("YouTube Mashup Generator")

    api_key = 'AIzaSyAJq5t7IavGMSQQTuUdOtaYjMh4lO4Lzp0'
    singer_name = st.text_input("Enter singer name:")
    num_videos = st.number_input(
        "Enter number of videos to download:", min_value=1, step=1)
    audio_duration = st.number_input(
        "Enter audio duration (in seconds):", min_value=1, step=1)
    output_filename = st.text_input("Enter output file name:")
    email_address = st.text_input("Enter your email address:")

    if st.button("Generate Mashup"):
        mashup(api_key, singer_name, num_videos,
               audio_duration, output_filename, email_address)
