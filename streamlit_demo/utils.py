import streamlit as st
import base64
from PIL import Image
import time
from io import BytesIO

from video_labeling.utils import extract_frames_from_video
from config import VIDEO_PATH


def show_video(task_name, task_df):
    global img_placeholder
    task = task_df[task_df["task_name"] == task_name].iloc[0]

    frames = extract_frames_from_video(
        VIDEO_PATH, int(task["start_frame"]), int(task["end_frame"]), 10
    )

    if img_placeholder is None:
        img_placeholder = st.empty()

    display_video(frames)


def display_video(frames):
    global img_placeholder
    for frame in frames:
        img_data = base64.b64decode(frame)
        img = Image.open(BytesIO(img_data))
        img_placeholder.image(img, use_column_width=True)
        time.sleep(0.1)
