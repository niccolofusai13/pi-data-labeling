import json
import asyncio
from openai import AsyncOpenAI
import os
import cv2

from config import RESULTS_OUTPUT_PATH, OPENAI_API_KEY, FRAMES_SEGMENT_SIZE, VIDEO_PATH

from video_labeling.detect_objects import identify_moved_objects
from video_labeling.label_actions import label_actions_in_episode
from video_labeling.label_frames import (
    label_episode_frame_ranges,
    adjusting_frames_in_episode,
)
from video_labeling.checks import (
    check_episode_frame_number_labels,
)
FRAMES_SEGMENT_SIZE = 250   
video_path = VIDEO_PATH
# video_path = "/Users/niccolofusai/Documents/pi/data/input/pi_video_test.mp4"

client = AsyncOpenAI(api_key=OPENAI_API_KEY)

def load_from_file(directory, filename):
    """Load JSON data from a specified file."""
    file_path = os.path.join(directory, filename)
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return None  # Return None or raise an exception if the file does not exist.

    with open(file_path, 'r') as f:
        data = json.load(f)
    print(f"Data loaded from {file_path}")
    return data


def save_to_file(data, directory, filename):
    os.makedirs(directory, exist_ok=True)  # Ensure the directory exists
    file_path = os.path.join(directory, filename)
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)
    print(f"Data saved to {file_path}")

def split_video_into_chunks(video_path, overlap=50):
    """
    Splitting video into smaller chunks with a sliding window overlap.

    Parameters:
        video_path (str): The path to the video file.
        frame_segment_size (int): The size of each frame segment.
        overlap (int): The number of frames to overlap between segments.

    Returns:
        list of tuples: Each tuple represents a (start_frame, end_frame) segment.
    """
    video = cv2.VideoCapture(video_path)
    total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    video.release()

    video_chunks = []
    # Start the first chunk at frame 0
    start_frame = 0

    while start_frame + FRAMES_SEGMENT_SIZE <= total_frames:
        end_frame = start_frame + FRAMES_SEGMENT_SIZE
        video_chunks.append((max(0, start_frame), min(total_frames, end_frame)))
        start_frame += (FRAMES_SEGMENT_SIZE - overlap)  # Move start frame forward, subtracting the overlap

    # Handle the last segment if the last chunk doesn't end at total_frames
    if start_frame < total_frames:
        video_chunks.append((max(0, start_frame), total_frames))

    return video_chunks

# def split_video_into_chunks(vidoe_path):
#     """Splitting video into smaller chunks"""
#     video = cv2.VideoCapture(vidoe_path)
#     total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
#     video.release()
#     video_chunks = [
#         (max(0, i - FRAMES_SEGMENT_SIZE), min(total_frames, i))
#         for i in range(
#             FRAMES_SEGMENT_SIZE, total_frames + FRAMES_SEGMENT_SIZE, FRAMES_SEGMENT_SIZE
#         )
#     ]

#     return video_chunks


async def label_video():    
    video_path = "/Users/niccolofusai/Documents/pi/data/input/val_1.mp4"

    base_name = os.path.splitext(os.path.basename(video_path))[0]
    base_name = "val_1"

    print(f"Step 0: Splitting video into smaller chunks...")
    video_chunks = split_video_into_chunks(video_path, overlap=50)
    save_to_file(video_chunks, f"results_folder/{base_name}", "video_chunks_new.json")
    # video_chunks = load_from_file(f"results_folder/{base_name}", "video_chunks_new.json")

    print(f"Step 1: Identifying which objects have moved...")
    moved_objects = await identify_moved_objects(
        client, video_path, video_chunks, fps=3
    )
    print(base_name)
    save_to_file(moved_objects, f"results_folder/{base_name}", "moved_objects_final.json")

    # moved_objects = load_from_file(f"results_folder/{base_name}", "moved_objects_new.json")


    # print(f"Step 2: Identifying which actions have taken place...")
    # labeled_actions = await label_actions_in_episode(
    #     client, video_path, moved_objects, video_chunks, fps=1
    # )
    # save_to_file(labeled_actions, f"results_folder/{base_name}", "labeled_actions.json")

    print(f"Step 3: Labeling the frame range...")
    labeled_frames = await label_episode_frame_ranges(
        client, video_path, labeled_actions, fps=5
    )

    print(f"Step 4: Running checks...")
    checks_feedback = await check_episode_frame_number_labels(
        client, video_path, labeled_frames, fps=5
    )

    print(f"Step 5: Iteratively refining labels until all checks pass...")
    final_results = await adjusting_frames_in_episode(
        client, video_path, checks_feedback, fps=5
    )

    print(f"Done... saving results...")
    output_file_path = os.path.join(RESULTS_OUTPUT_PATH, "test_results.json")
    with open(output_file_path, "w") as file:
        json.dump(final_results, file, indent=4)


if __name__ == "__main__":
    asyncio.run(label_video())
