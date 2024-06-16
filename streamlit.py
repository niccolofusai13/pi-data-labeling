import streamlit as st
import cv2 
import base64
import numpy as np
from PIL import Image
import time
import pandas as pd
from io import BytesIO

def extract_frames_from_video(video_path, start_frame, end_frame, fps=10):
    base64Frames = []
    video = cv2.VideoCapture(video_path)
    video_fps = video.get(cv2.CAP_PROP_FPS)

    frames_to_skip = max(int(video_fps / fps), 1)
    curr_frame = start_frame

    while curr_frame < end_frame:
        video.set(cv2.CAP_PROP_POS_FRAMES, curr_frame)
        success, frame = video.read()
        if not success:
            break
        _, buffer = cv2.imencode(".jpg", frame)
        base64Frames.append(base64.b64encode(buffer).decode("utf-8"))
        curr_frame += frames_to_skip

    video.release()

    return base64Frames

tasks = [{'task_name': 'Pick up Glass Bowl',
  'start_frame_of_segment': 0.0,
  'end_frame_of_segment': 160.0,
  'start_image': 6,
  'end_image': 22,
  'start_frame': 30.0,
  'end_frame': 132.0,
  'fps': 5,
  'task_type': 'pick'},
 {'task_name': 'Put Glass Bowl into Clear Plastic Box',
  'start_frame_of_segment': 100.0,
  'end_frame_of_segment': 180.0,
  'start_image': 2,
  'end_image': 12,
  'start_frame': 106.0,
  'end_frame': 172.0,
  'fps': 5,
  'task_type': 'put'},
 {'task_name': 'Pick up Cardboard Food Container',
  'start_frame_of_segment': 240.0,
  'end_frame_of_segment': 270.0,
  'start_image': 1,
  'end_image': 8,
  'start_frame': 240.0,
  'end_frame': 264.0,
  'fps': 10,
  'task_type': 'pick'},
 {'task_name': 'Put Cardboard Food Container into Blue Trash Bin',
  'start_frame_of_segment': 180.0,
  'end_frame_of_segment': 260.0,
  'start_image': 6,
  'end_image': 12,
  'start_frame': 210.0,
  'end_frame': 252.0,
  'fps': 5,
  'task_type': 'put'},
 {'task_name': 'Pick up Orange Plate',
  'start_frame_of_segment': 310.0,
  'end_frame_of_segment': 390.0,
  'start_image': 1,
  'end_image': 8,
  'start_frame': 310.0,
  'end_frame': 358.0,
  'fps': 5,
  'task_type': 'pick'},
 {'task_name': 'Put Orange Plate into Clear Plastic Box',
  'start_frame_of_segment': 310.0,
  'end_frame_of_segment': 380.0,
  'start_image': 4,
  'end_image': 11,
  'start_frame': 328.0,
  'end_frame': 376.0,
  'fps': 5,
  'task_type': 'put'},
 {'task_name': 'Pick up Plastic Bowl',
  'start_frame_of_segment': 440.0,
  'end_frame_of_segment': 480.0,
  'start_image': 1,
  'end_image': 10,
  'start_frame': 440.0,
  'end_frame': 470.0,
  'fps': 10,
  'task_type': 'pick'},
 {'task_name': 'Put Plastic Bowl into Clear Plastic Box',
  'start_frame_of_segment': 450.0,
  'end_frame_of_segment': 530.0,
  'start_image': 2,
  'end_image': 9,
  'start_frame': 456.0,
  'end_frame': 504.0,
  'fps': 5,
  'task_type': 'put'},
 {'task_name': 'Pick up Metal Spoon',
  'start_frame_of_segment': 480.0,
  'end_frame_of_segment': 720.0,
  'start_image': 1,
  'end_image': 20,
  'start_frame': 480.0,
  'end_frame': 680.0,
  'fps': 3,
  'task_type': 'pick'},
 {'task_name': 'Put Metal Spoon into Clear Plastic Box',
  'start_frame_of_segment': 710.0,
  'end_frame_of_segment': 760.0,
  'start_image': 2,
  'end_image': 9,
  'start_frame': 713.0,
  'end_frame': 737.0,
  'fps': 10,
  'task_type': 'put'},
 {'task_name': 'Pick up Aluminum Container',
  'start_frame_of_segment': 760.0,
  'end_frame_of_segment': 840.0,
  'start_image': 1,
  'end_image': 8,
  'start_frame': 760.0,
  'end_frame': 808.0,
  'fps': 5,
  'task_type': 'pick'},
 {'task_name': 'Put Aluminum Container into Blue Trash Bin',
  'start_frame_of_segment': 800.0,
  'end_frame_of_segment': 850.0,
  'start_image': 2,
  'end_image': 11,
  'start_frame': 803.0,
  'end_frame': 833.0,
  'fps': 10,
  'task_type': 'put'},
 {'task_name': 'Pick up Black Chopstick',
  'start_frame_of_segment': 760.0,
  'end_frame_of_segment': 1040.0,
  'start_image': 1,
  'end_image': 6,
  'start_frame': 760.0,
  'end_frame': 820.0,
  'fps': 3,
  'task_type': 'pick'},
 {'task_name': 'Put Black Chopstick into Clear Plastic Box',
  'start_frame_of_segment': 1030.0,
  'end_frame_of_segment': 1100.0,
  'start_image': 2,
  'end_image': 12,
  'start_frame': 1036.0,
  'end_frame': 1102.0,
  'fps': 5,
  'task_type': 'put'}]

def display_video(frames):
    img_placeholder = st.empty()
    
    # Iterate over each frame and update the display
    for frame in frames:
        img_data = base64.b64decode(frame)
        img = Image.open(BytesIO(img_data))
        img_placeholder.image(img, use_column_width=True)
        time.sleep(0.1)  # Adjust frame rate as needed

# Streamlit layout
st.title('Robot Task Video Analysis')

# Display task data in a table and handle selection
task_df = pd.DataFrame(tasks)
task_df['duration'] = task_df['end_frame'] - task_df['start_frame']
st.dataframe(task_df[['task_name', 'start_frame', 'end_frame', 'duration']])

task_name = task_df['task_name'].unique()
selected_task_name = st.selectbox('Select a task to view:', task_name)


# selected_idx = st.selectbox('Select an episode to view:', range(len(tasks)))

if st.button('Show Video'):
    task = task_df[task_df['task_name'] == selected_task_name].iloc[0]

    VIDEO_PATH = "test2.mp4"  # Specify the path to your video file
    frames = extract_frames_from_video(VIDEO_PATH, task['start_frame'], task['end_frame'], 10)
    display_video(frames)


