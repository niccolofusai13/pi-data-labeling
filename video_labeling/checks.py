import asyncio
import copy

from video_labeling.utils import extract_frames_from_video
from video_labeling.prompts.shared import SYSTEM_PROMPT

from video_labeling.prompts.reflection_checks import (
    VIDEO_DESCRIPTION,
    CHECK_WRONG_ACTION,
    CHECK_PICKUP_START_IMAGE_TIMING,
    CHECK_PICKUP_END_IMAGE_TIMING,
    CHECK_DEPOSIT_START_IMAGE_TIMING,
    CHECK_DEPOSIT_END_IMAGE_TIMING,
)

from video_labeling.utils import (
    vlm_request,
    extract_json_from_response,
    adjust_fps_to_frame_count,
)


def create_check_prompts(task_type, task_name, object_name):
    """Creating the prompt template to run the checks"""
    if task_type == "pick":
        start_prompt = CHECK_PICKUP_START_IMAGE_TIMING.format(
            action=task_name, object=object_name
        )
        end_prompt = CHECK_PICKUP_END_IMAGE_TIMING.format(
            action=task_name, object=object_name
        )
    elif task_type == "put":
        start_prompt = CHECK_DEPOSIT_START_IMAGE_TIMING.format(
            action=task_name, object=object_name
        )
        end_prompt = CHECK_DEPOSIT_END_IMAGE_TIMING.format(
            action=task_name, object=object_name
        )
    else:
        raise ValueError(f"Unsupported task type: {task_type}")
    return start_prompt, end_prompt


async def determine_erroneous_action(action, client, video_path, fps=5):
    """Determining if an action doesn't match the description label"""

    start_frame, end_frame = action["start_frame"], action["end_frame"]

    frames = extract_frames_from_video(video_path, start_frame, end_frame, fps=fps)
    video_description = await vlm_request(
        client, SYSTEM_PROMPT, VIDEO_DESCRIPTION, frames, extract_json=False
    )

    prompt = CHECK_WRONG_ACTION.format(
        action=action["action"],
        object=action["object"],
        description=video_description,
    )
    wrong_object_response = await vlm_request(
        client, SYSTEM_PROMPT, prompt, frames, extract_json=False
    )

    return {
        "action": action["action"],
        "start_frame": start_frame,
        "end_frame": end_frame,
        "fps": fps,
        "action_type": action["action_type"],
        "object": action["object"],
        "wrong_object": wrong_object_response,
    }


async def remove_erroneous_actions(client, video_path, labeled_timesteps, fps=5):
    """Getting rid of all erroneous actions in an episode"""
    tasks_to_process = [
        determine_erroneous_action(copy.deepcopy(action), client, video_path, fps=fps) for action in labeled_timesteps
    ]
    responses = await asyncio.gather(*tasks_to_process)
    return [task for task in responses if task["wrong_object"] != "Yes"]


async def check_action_frame_number_labels(action, client, video_path, fps=5):
    """Check timing  """
    start_frame, end_frame = action["start_frame"], action["end_frame"]

    frames, _ = adjust_fps_to_frame_count(
        video_path, start_frame, end_frame, fps, 5, 20
    )

    start_prompt, end_prompt = create_check_prompts(
        action["action_type"], action["action"], action["object"]
    )
    start_response = await vlm_request(
        client, SYSTEM_PROMPT, start_prompt, frames, extract_json=False
    )
    end_response = await vlm_request(
        client, SYSTEM_PROMPT, end_prompt, frames, extract_json=False
    )

    action.update(
        {
            "start_answer": start_response,
            "end_answer": end_response,
            "start_check": extract_json_from_response(start_response)["answer"],
            "end_check": extract_json_from_response(end_response)["answer"],
        }
    )

    return action


async def check_episode_frame_number_labels(client, video_path, labeled_actions, fps=5):
    tasks_to_process = [check_action_frame_number_labels(copy.deepcopy(action), client, video_path, fps=fps) for action in labeled_actions]
    responses = await asyncio.gather(*tasks_to_process)
    return responses
