import asyncio
import copy

from config import FPS_OPTIONS
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


async def label_episode_frame_ranges(client, video_path, labeled_actions, fps=5):
    tasks_to_process = []
    for action in labeled_actions:
        tasks_to_process.append(
            label_action_frame_range(client, video_path, copy.deepcopy(action), fps)
        )

    responses = await asyncio.gather(*tasks_to_process)
    filtered_responses = [response for response in responses if response is not None]

    return filtered_responses


async def label_action_frame_range(client, video_path, action_dict, fps):
    """Process a single robot task by calculating the range, getting frames, and analyzing the task."""
    video_fps = 30
    # sequence_fps = 5
    buffer_multiplier = 2

    expanded_start, expanded_end = calculate_expanded_range(action_dict['start_frame'], action_dict['end_frame'], buffer_multiplier=buffer_multiplier)
    
    frames = extract_frames_from_video(
        video_path, start_frame=expanded_start, end_frame=expanded_end, fps=fps
    )

    # We want to make sure images are between the desired amount of 8 - 18
    while not (8 <= len(frames) <= 18):
        if len(frames) < 8:
            # Increase fps to the next higher option if below the minimum frame count
            current_index = FPS_OPTIONS.index(fps)
            if current_index < len(FPS_OPTIONS) - 1:
                fps = FPS_OPTIONS[current_index + 1]
            else:
                # If already at max fps and frames are still not enough, exit the loop
                break
        elif len(frames) > 18:
            # Decrease fps to the next lower option if above the maximum frame count
            current_index = FPS_OPTIONS.index(fps)
            if current_index > 0:
                fps = FPS_OPTIONS[current_index - 1]
            else:
                # If already at minimum fps and frames are still too many, exit the loop
                break

        frames = extract_frames_from_video(
            video_path,
            start_frame=expanded_start,
            end_frame=expanded_end,
            fps=fps,
        )


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
    

    start_frame = expanded_start + (start_image_number - 1) * video_fps / fps
    end_frame = expanded_start + (end_image_number) * video_fps / fps

    result = {
        "action": action_dict["action"],
        "start_image": start_image_number,
        "end_image": end_image_number,
        "start_frame": start_frame,
        "end_frame": end_frame,
        "fps": fps,
        "action_type": action_dict["action_type"],
        "object": action_dict["object"],
    }

    return result





async def adjust_frames_for_action(action_dict, client, video_path, fps):
    """Process a single robot task by calculating the range, getting frames, and analyzing the task."""
    action_type = action_dict["action_type"]
    object_name = action_dict["object"]
    start_frame, end_frame = (
        action_dict["modified_start_frame"],
        action_dict["modified_end_frame"],
    )
    need_modification = action_dict["need_modification"]

    if not need_modification:
        return action_dict

    while need_modification:
        frames = extract_frames_from_video(
            video_path, start_frame=start_frame, end_frame=end_frame, fps=fps
        )

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


async def adjusting_frames_in_episode(client, video_path, labeled_results, fps=5):
    adjusted_tasks = adjust_task_frames(labeled_results)

    tasks_to_process = [adjust_frames_for_action(copy.deepcopy(action), client, video_path, fps) for action in adjusted_tasks]
    responses = await asyncio.gather(*tasks_to_process)
    return responses



