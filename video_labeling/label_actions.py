import cv2
import asyncio
from openai import AsyncOpenAI

from config import (
    OPENAI_API_KEY,
    VIDEO_PATH,
    FRAMES_SEGMENT_SIZE,
)
from video_labeling.utils import extract_frames_from_video
from video_labeling.prompts.shared import SYSTEM_PROMPT
from video_labeling.prompts.label_actions import LABEL_ACTIONS

from video_labeling.utils import (
    vlm_request,
    add_task_type,
)

client = AsyncOpenAI(api_key=OPENAI_API_KEY)


async def label_actions_in_episode(moved_objects):
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
    for (start, end), change in zip(frame_ranges, moved_objects):
        if change:
            moved_objects_string = ", ".join(change["moved_objects"])

            label_action_prompt = LABEL_ACTIONS.format(
                moved_objects=moved_objects_string
            )

            task = vlm_request(
                client,
                SYSTEM_PROMPT,
                label_action_prompt,
                extract_frames_from_video(VIDEO_PATH, start, end, fps=1),
                extract_json=True,
            )
            tasks.append(task)

    second_round_responses = await asyncio.gather(*tasks)

    actions_with_frame_ranges = [
        {"frame_range": f"{start}-{end}", "actions": response}
        for ((start, end), response) in zip(frame_ranges, second_round_responses)
    ]

    labeled_actions = add_task_type(actions_with_frame_ranges)

    return labeled_actions
