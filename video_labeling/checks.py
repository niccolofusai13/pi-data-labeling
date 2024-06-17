import asyncio
from openai import AsyncOpenAI

from config import (
    OPENAI_API_KEY,
    VIDEO_PATH,
)
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

client = AsyncOpenAI(api_key=OPENAI_API_KEY)


# async def determine_erroneous_action(video_path, action):
#     """Process a single robot task by calculating the range, getting frames, and analyzing the task."""
#     task_name = action["task_name"]
#     task_type = action["task_type"]
#     object = action["object"]
#     start_frame, end_frame = action["start_frame"], action["end_frame"]
#     sequence_fps = 5

#     frames = extract_frames_from_video(
#         video_path, start_frame=start_frame, end_frame=end_frame, fps=sequence_fps
#     )

#     video_description = await vlm_request(
#         client, SYSTEM_PROMPT, VIDEO_DESCRIPTION, frames, extract_json=False
#     )

#     prompt = CHECK_WRONG_ACTION.format(
#         action=task_name, object=object, description=video_description
#     )
#     wrong_object_response = await vlm_request(
#         client, SYSTEM_PROMPT, prompt, frames, extract_json=False
#     )

#     result = {
#         "task_name": task_name,
#         "start_frame": start_frame,
#         "end_frame": end_frame,
#         "fps": sequence_fps,
#         "task_type": task_type,
#         "object": action["object"],
#         "wrong_object": wrong_object_response,
#     }

#     return result


# async def remove_erroneous_actions(labeled_timesteps):
#     tasks_to_process = []
#     for action in labeled_timesteps:
#         tasks_to_process.append(determine_erroneous_action(VIDEO_PATH, action))
#     responses = await asyncio.gather(*tasks_to_process)
#     filtered_tasks_test = [task for task in responses if task["wrong_object"] != "Yes"]

#     return filtered_tasks_test

# def generate_check_prompts_based_on_task_type(task_details):
#     """Generate different prompts based on the task type."""
#     if task_details["task_type"] == "pick":
#         start_prompt = CHECK_PICKUP_START_IMAGE_TIMING.format(action=task_details["task_name"], object=task_details["object_name"])
#         end_prompt = CHECK_PICKUP_END_IMAGE_TIMING.format(action=task_details["task_name"], object=task_details["object_name"])
#     elif task_details["task_type"] == "put":
#         start_prompt = CHECK_DEPOSIT_START_IMAGE_TIMING.format(action=task_details["task_name"], object=task_details["object_name"])
#         end_prompt = CHECK_DEPOSIT_END_IMAGE_TIMING.format(action=task_details["task_name"], object=task_details["object_name"])
#     else:
#         raise ValueError(f"Unsupported task type: {task_details['task_type']}")
#     return start_prompt, end_prompt


# async def run_action_check(action):
#     """Process a single robot task by calculating the range, getting frames, and analyzing the task."""
#     task_name = action["task_name"]
#     task_type = action["task_type"]
#     object_name = action["object"]
#     start_frame, end_frame = action["start_frame"], action["end_frame"]
#     sequence_fps = 5  # Assuming a fixed FPS for extraction

#     frames, _ = adjust_fps_to_frame_count(
#         VIDEO_PATH, start_frame, end_frame, sequence_fps, 5, 20
#     )

#     # Determine prompts based on task type
#     if task_type == "pick":
#         start_prompt = CHECK_PICKUP_START_IMAGE_TIMING.format(
#             action=task_name, object=object_name
#         )
#         end_prompt = CHECK_PICKUP_END_IMAGE_TIMING.format(
#             action=task_name, object=object_name
#         )
#     elif task_type == "put":
#         start_prompt = CHECK_DEPOSIT_START_IMAGE_TIMING.format(
#             action=task_name, object=object_name
#         )
#         end_prompt = CHECK_DEPOSIT_END_IMAGE_TIMING.format(
#             action=task_name, object=object_name
#         )
#     else:
#         raise ValueError(f"Unsupported task type: {task_type}")

#     # Request analysis for start and end frames
#     start_response = await vlm_request(
#         client, SYSTEM_PROMPT, start_prompt, frames, temperature=0, extract_json=False
#     )
#     end_response = await vlm_request(
#         client, SYSTEM_PROMPT, end_prompt, frames, temperature=0, extract_json=False
#     )

#     start_check = extract_json_from_response(start_response)["answer"]
#     end_check = extract_json_from_response(end_response)["answer"]

#     action["start_answer"] = start_response
#     action["end_answer"] = end_response
#     action["start_check"] = start_check
#     action["end_check"] = end_check

#     return action


# async def run_checks(tasks):
#     tasks_to_process = [run_action_check(action, fps=fps) for action in tasks]
#     responses = await asyncio.gather(*tasks_to_process)
#     return responses




"""

---------------------------------------------------------------------------------------------------------

"""


async def determine_erroneous_action(video_path, action):
    start_frame, end_frame = action["start_frame"], action["end_frame"]
    sequence_fps = 5

    frames = extract_frames_from_video(video_path, start_frame, end_frame, sequence_fps)
    video_description = await vlm_request(client, SYSTEM_PROMPT, VIDEO_DESCRIPTION, frames)

    prompt = CHECK_WRONG_ACTION.format(action=action["task_name"], object=action["object"], description=video_description)
    wrong_object_response = await vlm_request(client, SYSTEM_PROMPT, prompt, frames)

    return {
        "task_name": action["task_name"],
        "start_frame": start_frame,
        "end_frame": end_frame,
        "fps": sequence_fps,
        "task_type": action["task_type"],
        "object": action["object"],
        "wrong_object": wrong_object_response,
    }


async def remove_erroneous_actions(labeled_timesteps, fps=5):
    tasks_to_process = [determine_erroneous_action(action, fps=fps) for action in labeled_timesteps]
    responses = await asyncio.gather(*tasks_to_process)
    return [task for task in responses if task["wrong_object"] != "Yes"]


def create_check_prompts(task_type, task_name, object_name):
    if task_type == "pick":
        start_prompt = CHECK_PICKUP_START_IMAGE_TIMING.format(action=task_name, object=object_name)
        end_prompt = CHECK_PICKUP_END_IMAGE_TIMING.format(action=task_name, object=object_name)
    elif task_type == "put":
        start_prompt = CHECK_DEPOSIT_START_IMAGE_TIMING.format(action=task_name, object=object_name)
        end_prompt = CHECK_DEPOSIT_END_IMAGE_TIMING.format(action=task_name, object=object_name)
    else:
        raise ValueError(f"Unsupported task type: {task_type}")
    return start_prompt, end_prompt

async def run_action_check(action, fps=5):

    start_frame, end_frame = action["start_frame"], action["end_frame"]
    frames, _ = adjust_fps_to_frame_count(start_frame, end_frame, fps, 5, 20)

    start_prompt, end_prompt = create_check_prompts(action["task_type"], action["task_name"], action["object"])
    start_response = await vlm_request(client, SYSTEM_PROMPT, start_prompt, frames)
    end_response = await vlm_request(client, SYSTEM_PROMPT, end_prompt, frames)

    action.update({
        "start_answer": start_response,
        "end_answer": end_response,
        "start_check": extract_json_from_response(start_response)["answer"],
        "end_check": extract_json_from_response(end_response)["answer"]
    })

    return action


async def run_checks(tasks, fps=5):
    tasks_to_process = [run_action_check(action, fps=fps) for action in tasks]
    responses = await asyncio.gather(*tasks_to_process)
    return responses