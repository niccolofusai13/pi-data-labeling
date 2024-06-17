import streamlit as st
import pandas as pd
import json

# from utils import show_video
from config import STREAMLIT_RESULTS_PATH


with open(STREAMLIT_RESULTS_PATH, "r") as file:
    tasks = json.load(file)

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


st.title("Robot Task Video Analysis")
st.write(
    "The data labeling process in the example below is completely autonomous. \n The only input is the mp4 video."
)

task_df = pd.DataFrame(tasks)
task_df["duration"] = task_df["end_frame"] - task_df["start_frame"]
st.dataframe(task_df[["task_name", "start_frame", "end_frame", "duration"]])

img_placeholder = None


selected_task_name = st.selectbox(
    "Select a task to view:",
    task_df["task_name"].unique(),
    index=0,
    on_change=lambda: show_video(st.session_state["selected_task_name"], task_df),
    key="selected_task_name",
)

show_video(selected_task_name, task_df)

# # Streamlit layout
# st.title("PI Automated Data Labeling Demo")
# st.write(
#     "The data labeling process in the example below is fully autonomous. \n\n The only input is the mp4 video. "
# )

# # Display task data in a table and handle selection
# task_df = pd.DataFrame(tasks)  # Ensure 'tasks' is defined or fetched appropriately
# task_df["duration"] = task_df["end_frame"] - task_df["start_frame"]
# st.dataframe(task_df[["task_name", "start_frame", "end_frame", "duration"]])

# # Dropdown for selecting a task, automatically updates on change
# selected_task_name = st.selectbox(
#     "Select a task to view:",
#     task_df["task_name"].unique(),
#     on_change=lambda: show_video(selected_task_name, task_df),
# )


# def show_video(selected_task_name, task_df):
#     # Find the task details based on selected task name
#     task = task_df[task_df["task_name"] == selected_task_name].iloc[0]

#     # Extract frames for the selected task
#     frames = extract_frames_from_video(
#         VIDEO_PATH,
#         int(task["start_frame"]),
#         int(task["end_frame"]),
#         10,  # or adjust fps as needed
#     )

#     # Display the video frames
#     display_video(frames)


# def display_video(frames):
#     img_placeholder = st.empty()

#     # Iterate over each frame and update the display
#     for frame in frames:
#         img_data = base64.b64decode(frame)
#         img = Image.open(BytesIO(img_data))
#         img_placeholder.image(img, use_column_width=True)
#         time.sleep(0.1)  # Adjust frame rate as needed


# # Initial call to show video for the default selected task
# show_video(selected_task_name, task_df)
