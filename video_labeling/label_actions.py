import cv2
import asyncio
from openai import AsyncOpenAI

from config import (
    OPENAI_API_KEY,
)
from video_labeling.utils import extract_frames_from_video
from video_labeling.prompts.shared import SYSTEM_PROMPT
from video_labeling.prompts.label_actions import LABEL_ACTIONS

from video_labeling.utils import (
    vlm_request
)

client = AsyncOpenAI(api_key=OPENAI_API_KEY)

def add_action_type(action_dict): 
    """Add type of action: 'pick' or 'put' to the action_dict """
    first_word = action_dict['action'].split()[0].lower()
    if "pick" == first_word:
        action_dict["action_type"] = "pick"
    elif "put" == first_word:
        action_dict["action_type"] = "put"
    else:
        raise ValueError(
            f"Action description does not start with 'Pick' or 'Put': {action_dict['action']}"
        )
    return action_dict

async def label_actions_in_episode(client, video_path, moved_objects, video_chunks):
    """Labeling which actions took place for each video chunk in an episode"""
    fps = 1
    tasks = []
    for (start, end), change in zip(video_chunks, moved_objects):
        if change:
            moved_objects_string = ", ".join(change["moved_objects"])
            label_action_prompt = LABEL_ACTIONS.format(
                moved_objects=moved_objects_string
            )
            task = vlm_request(
                client,
                SYSTEM_PROMPT,
                label_action_prompt,
                extract_frames_from_video(video_path, start, end, fps=1),
                extract_json=True,
            )
            tasks.append(task)
    labeled_actions = await asyncio.gather(*tasks)

    actions_with_frame_ranges=[]
    for ((start_segment_frame, _), response) in zip(video_chunks, labeled_actions):
        for action_dict in response['tasks']:
            start_image_number, end_image_number = int(action_dict['start_image']), int(action_dict['end_image']), 
            start_frame = int(start_segment_frame) + (start_image_number - 1) * 30 / fps
            end_frame = int(start_segment_frame) + (end_image_number) * 30 / fps
            action_dict.update({
                'start_frame': start_frame,
                'end_frame': end_frame,
                'start_image': start_image_number,
                'end_image': end_image_number, 
                'fps': fps
            })
            action_dict = add_action_type(action_dict)
            actions_with_frame_ranges.append(action_dict)

    return actions_with_frame_ranges