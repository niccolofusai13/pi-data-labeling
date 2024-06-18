import asyncio
from openai import AsyncOpenAI

from config import OPENAI_API_KEY, VIDEO_PATH, FPS_OPTIONS
from video_labeling.utils import extract_frames_from_video
from video_labeling.prompts.shared import SYSTEM_PROMPT
from video_labeling.prompts.label_frames import (
    REFINED_START_FRAME_PICK,
    REFINED_END_FRAME_PICK,
    REFINED_START_FRAME_DEPOSIT,
    REFINED_END_FRAME_DEPOSIT,
    LABEL_PICKUP_ACTION,
    LABEL_DEPOSIT_ACTION
)
from video_labeling.prompts.reflection_checks import (
    CHECK_PICKUP_START_IMAGE_TIMING,
    CHECK_PICKUP_END_IMAGE_TIMING,
    CHECK_DEPOSIT_START_IMAGE_TIMING,
    CHECK_DEPOSIT_END_IMAGE_TIMING,
)

from video_labeling.utils import (
    adjust_task_frames,
    vlm_request,
    calculate_expanded_range,
)

client = AsyncOpenAI(api_key=OPENAI_API_KEY)


async def label_episode_frame_ranges(labeled_actions):
    tasks_to_process = []
    for action in labeled_actions:
        tasks_to_process.append(
            label_action_frame_range(VIDEO_PATH, action, action['start_frame'])
        )

    responses = await asyncio.gather(*tasks_to_process)
    filtered_responses = [response for response in responses if response is not None]

    return filtered_responses


async def label_action_frame_range(video_path, action_dict, start_frame_of_segment):
    """Process a single robot task by calculating the range, getting frames, and analyzing the task."""
    video_fps = 30
    sequence_fps = 5
    buffer_multiplier = 2

    expanded_start, expanded_end = calculate_expanded_range(action_dict['start_frame'], action_dict['end_frame'], buffer_multiplier=buffer_multiplier)
    
    frames = extract_frames_from_video(
        video_path, start_frame=expanded_start, end_frame=expanded_end, fps=sequence_fps
    )
    num_images = len(frames)

    while True:
        frames = extract_frames_from_video(
            video_path,
            start_frame=expanded_start,
            end_frame=expanded_end,
            fps=sequence_fps,
        )
        num_images = len(frames)

        if num_images < 8:
            # Increase fps to the next higher option if below the minimum frame count
            current_index = FPS_OPTIONS.index(sequence_fps)
            if current_index < len(FPS_OPTIONS) - 1:
                sequence_fps = FPS_OPTIONS[current_index + 1]
            else:
                # If already at max fps and frames are still not enough, break the loop
                break
        elif num_images > 18:
            # Decrease fps to the next lower option if above the maximum frame count
            current_index = FPS_OPTIONS.index(sequence_fps)
            if current_index > 0:
                sequence_fps = FPS_OPTIONS[current_index - 1]
            else:
                # If already at minimum fps and frames are still too many, break the loop
                break
        else:
            # If the number of frames is within the acceptable range, break the loop
            break


    if action_dict["action_type"] == "pick":
        timestep_prompt = LABEL_PICKUP_ACTION.format(
            action=action_dict["action"], object=action_dict["object"]
        )
    else:
        timestep_prompt = LABEL_DEPOSIT_ACTION.format(
            action=action_dict["action"], object=action_dict["object"]
        )

    response = await vlm_request(
        client, SYSTEM_PROMPT, timestep_prompt, frames, temperature=0, extract_json=True
    )

    if response is None:
            return None

    start_image_number = int(response.get("start_image", None)) or None
    end_image_number = int(response.get("end_image", None)) or None

    if not start_image_number or not end_image_number: 
        return None
    

    start_frame = expanded_start + (start_image_number - 1) * video_fps / sequence_fps
    end_frame = expanded_start + (end_image_number) * video_fps / sequence_fps

    result = {
        "action": action_dict["action"],
        "start_image": start_image_number,
        "end_image": end_image_number,
        "start_frame": start_frame,
        "end_frame": end_frame,
        "fps": sequence_fps,
        "action_type": action_dict["action_type"],
        "object": action_dict["object"],
    }

    return result





async def adjust_frames_for_action(action_dict):
    """Process a single robot task by calculating the range, getting frames, and analyzing the task."""
    action_type = action_dict["action_type"]
    object_name = action_dict["object"]
    start_frame, end_frame = (
        action_dict["modified_start_frame"],
        action_dict["modified_end_frame"],
    )
    sequence_fps = 5  # Assuming a fixed FPS for extraction
    need_modification = action_dict["need_modification"]

    if not need_modification:
        return action_dict

    while need_modification:
        # Extract frames for analysis
        frames = extract_frames_from_video(
            VIDEO_PATH, start_frame=start_frame, end_frame=end_frame, fps=sequence_fps
        )

        # Determine prompts based on task type
        if action_type == "pick":
            start_prompt = REFINED_START_FRAME_PICK.format(
                action=action_dict, object=object_name
            )
            end_prompt = REFINED_END_FRAME_PICK.format(
                action=action_dict, object=object_name
            )
            start_check_prompt = CHECK_PICKUP_START_IMAGE_TIMING.format(
                action=action_dict, object=object_name
            )
            end_check_prompt = CHECK_PICKUP_END_IMAGE_TIMING.format(
                action=action_dict, object=object_name
            )
        elif action_type == "put":
            start_prompt = REFINED_START_FRAME_DEPOSIT.format(
                action=action_dict, object=object_name
            )
            end_prompt = REFINED_END_FRAME_DEPOSIT.format(
                action=action_dict, object=object_name
            )
            start_check_prompt = CHECK_DEPOSIT_START_IMAGE_TIMING.format(
                action=action_dict, object=object_name
            )
            end_check_prompt = CHECK_DEPOSIT_END_IMAGE_TIMING.format(
                action=action_dict, object=object_name
            )
        else:
            raise ValueError(f"Unsupported task type: {action_type}")

        if action_dict["start_check"] != "perfect":
            start_frame = await vlm_request(
                client,
                SYSTEM_PROMPT,
                start_prompt,
                frames,
                temperature=0,
                extract_json=True,
            )
            action_dict["modified_start_frame"] = start_frame.get("answer", "perfect")
            check_response = await vlm_request(
                client,
                SYSTEM_PROMPT,
                start_check_prompt,
                frames,
                temperature=0,
                extract_json=True,
            )
            action_dict["start_check"] = check_response["answer"]

        if action_dict["end_check"] != "perfect":
            end_frame = await vlm_request(
                client,
                SYSTEM_PROMPT,
                end_prompt,
                frames,
                temperature=0,
                extract_json=True,
            )
            action_dict["modified_end_frame"] = end_frame.get("answer", "perfect")
            check_response = await vlm_request(
                client,
                SYSTEM_PROMPT,
                end_check_prompt,
                frames,
                temperature=0,
                extract_json=True,
            )
            action_dict["end_check"] = check_response["answer"]

        # Re-evaluate need for modification
        action_dict["need_modification"] = (
            action_dict["start_check"] != "perfect" or action_dict["end_check"] != "perfect"
        )

        return action_dict


async def adjusting_frames_in_episode(tasks):
    adjusted_tasks = adjust_task_frames(tasks)

    tasks_to_process = [adjust_frames_for_action(action) for action in adjusted_tasks]
    responses = await asyncio.gather(*tasks_to_process)
    return responses



