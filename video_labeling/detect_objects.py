import cv2
import asyncio
from openai import AsyncOpenAI

from config import (
    OPENAI_API_KEY,
    VIDEO_PATH,
    FRAMES_SEGMENT_SIZE,
)
from video_labeling.utils import extract_frames_from_video
from video_labeling.prompts.find_objects import (
    FIND_OBJECTS_SYSTEM_PROMPT,
    FIND_OBJECTS,
)

from video_labeling.utils import (
    vlm_request,
)

client = AsyncOpenAI(api_key=OPENAI_API_KEY)


async def identify_moved_objects():
    video = cv2.VideoCapture(VIDEO_PATH)
    total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    video.release()
    frame_ranges = [
        (max(0, i - FRAMES_SEGMENT_SIZE), min(total_frames, i))
        for i in range(
            FRAMES_SEGMENT_SIZE, total_frames + FRAMES_SEGMENT_SIZE, FRAMES_SEGMENT_SIZE
        )
    ]

    tasks = []
    for start, end in frame_ranges:
        frames = extract_frames_from_video(VIDEO_PATH, start, end, fps=1)
        tasks.append(
            vlm_request(
                client,
                FIND_OBJECTS_SYSTEM_PROMPT,
                FIND_OBJECTS,
                frames,
                extract_json=True,
            )
        )

    moved_objects = await asyncio.gather(*tasks)

    return moved_objects
