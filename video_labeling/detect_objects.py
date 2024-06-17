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


async def identify_moved_objects(client, video_path, video_chunks):
    """Identifying which objects have moved positions in the chunks"""
    tasks = []
    for start, end in video_chunks:
        frames = extract_frames_from_video(video_path, start, end, fps=1)
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
