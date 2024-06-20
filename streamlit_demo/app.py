import streamlit as st
import pandas as pd
import json
import base64
from PIL import Image
import time
from io import BytesIO

from config import STREAMLIT_RESULTS_PATH, VIDEO_PATH
from video_labeling.utils import extract_frames_from_video


with open("data/output/test_results.json", "r") as file:
    results = json.load(file)


def show_video(task_name, task_df):
    global img_placeholder
    task = task_df[task_df["action"] == task_name].iloc[0]

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


st.title("Robot Task Video Analysis")
st.write(
    "The data labeling process in the example below is completely autonomous. \n The only input is the mp4 video."
)

task_df = pd.DataFrame(results)
task_df["duration"] = task_df["end_frame"] - task_df["start_frame"]
st.dataframe(task_df[["action", "start_frame", "end_frame", "duration"]])

img_placeholder = None


selected_task_name = st.selectbox(
    "Select an action to view:",
    task_df["action"].unique(),
    index=0,
    on_change=lambda: show_video(st.session_state["selected_action_name"], task_df),
    key="selected_action_name",
)

show_video(selected_task_name, task_df)

# # Streamlit layout
# st.title("PI Automated Data Labeling Demo")
# st.write(
#     "The data labeling process in the example below is fully autonomous. \n\n The only input is the mp4 video. "
# )

# task_df = pd.DataFrame(results)
# task_df["duration"] = task_df["end_frame"] - task_df["start_frame"]
# st.dataframe(task_df[["action", "start_frame", "end_frame", "duration"]])

# selected_task_name = st.selectbox(
#     "Select an action to view:",
#     task_df["action"].unique(),
#     on_change=lambda: show_video(selected_task_name, task_df),
# )


# def show_video(selected_task_name, task_df):
#     task = task_df[task_df["action"] == selected_task_name].iloc[0]

#     frames = extract_frames_from_video(
#         VIDEO_PATH,
#         int(task["start_frame"]),
#         int(task["end_frame"]),
#         10,
#     )

#     display_video(frames)


# def display_video(frames):
#     img_placeholder = st.empty()

#     for frame in frames:
#         img_data = base64.b64decode(frame)
#         img = Image.open(BytesIO(img_data))
#         img_placeholder.image(img, use_column_width=True)
#         time.sleep(0.1)


# show_video(selected_task_name, task_df)
