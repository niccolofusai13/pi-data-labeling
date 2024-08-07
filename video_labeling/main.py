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

video_path = VIDEO_PATH
client = AsyncOpenAI(api_key=OPENAI_API_KEY)


def split_video_into_chunks(vidoe_path):
    """Splitting video into smaller chunks"""
    video = cv2.VideoCapture(vidoe_path)
    total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    video.release()
    video_chunks = [
        (max(0, i - FRAMES_SEGMENT_SIZE), min(total_frames, i))
        for i in range(
            FRAMES_SEGMENT_SIZE, total_frames + FRAMES_SEGMENT_SIZE, FRAMES_SEGMENT_SIZE
        )
    ]

    return video_chunks


async def label_video():

    print(f"Step 0: Splitting video into smaller chunks...")
    video_chunks = split_video_into_chunks(video_path)

    print(f"Step 1: Identifying which objects have moved...")
    moved_objects = await identify_moved_objects(
        client, video_path, video_chunks, fps=1
    )

    print(f"Step 2: Identifying which actions have taken place...")
    labeled_actions = await label_actions_in_episode(
        client, video_path, moved_objects, video_chunks, fps=1
    )

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
