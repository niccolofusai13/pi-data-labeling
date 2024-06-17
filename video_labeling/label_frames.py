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
    LABEL_PICKUP_ACTION_HIGHER_FPS,
    LABEL_DEPOSIT_ACTION,
    LABEL_DEPOSIT_ACTION_HIGHER_FPS,
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


async def label_episode_frame_ranges(robot_actions):
    tasks_to_process = []
    for action_data in robot_actions:
        start_frame_of_segment = int(action_data["frame_range"].split("-")[0])
        for task in action_data["actions"]["tasks"]:
            tasks_to_process.append(
                label_action_frame_range(VIDEO_PATH, task, 30, start_frame_of_segment)
            )

    responses = await asyncio.gather(*tasks_to_process)
    return responses


async def label_action_frame_range(video_path, task, video_fps, start_frame_of_segment):
    """Process a single robot task by calculating the range, getting frames, and analyzing the task."""
    task_name = task["task"]
    image_range = task["image_range"]
    task_type = task["task_type"]
    start_img, end_img = map(int, image_range.split("-"))
    sequence_fps = 5
    prev_section_fps = 1

    expanded_start, expanded_end = calculate_expanded_range(
        start_frame_of_segment,
        video_fps,
        prev_section_fps,
        start_img,
        end_img,
        expansion_multiplier=3,
    )

    frames = extract_frames_from_video(
        video_path, start_frame=expanded_start, end_frame=expanded_end, fps=sequence_fps
    )
    num_images = len(frames)

    while True:  # Loop until the number of images is less than 20

        expanded_start, expanded_end = calculate_expanded_range(
            start_frame_of_segment,
            video_fps,
            prev_section_fps,
            start_img,
            end_img,
            expansion_multiplier=3,
        )

        frames = extract_frames_from_video(
            video_path,
            start_frame=expanded_start,
            end_frame=expanded_end,
            fps=sequence_fps,
        )
        num_images = len(frames)

        if num_images < 20:
            break

        # Reduce the fps by half and recompute if the number of images is 15 or more
        sequence_fps /= 2
        if (
            sequence_fps < 0.2
        ):  # Ensure fps does not become too low, can adjust this limit as needed
            break

    if task_type == "pick":
        timestep_prompt = LABEL_PICKUP_ACTION.format(
            action=task_name, object=task["object"]
        )
    else:
        timestep_prompt = LABEL_DEPOSIT_ACTION.format(
            action=task_name, object=task["object"]
        )

    response = await vlm_request(
        client, SYSTEM_PROMPT, timestep_prompt, frames, temperature=0, extract_json=True
    )

    start_image_number = int(response.get("start_image"))
    end_image_number = int(response.get("end_image"))

    start_frame = expanded_start + (start_image_number - 1) * video_fps / sequence_fps
    end_frame = expanded_start + (end_image_number) * video_fps / sequence_fps

    result = {
        "task_name": task_name,
        "start_frame_of_segment": expanded_start,
        "end_frame_of_segment": expanded_end,
        "start_image": response.get("start_image"),
        "end_image": response.get("end_image"),
        "start_frame": start_frame,
        "end_frame": end_frame,
        "fps": sequence_fps,
        "task_type": task_type,
        "object": task["object"],
    }

    return result


async def relabel_action_frames_with_higher_fps(video_path, action, video_fps):
    """Process a single robot task by calculating the range, getting frames, and analyzing the task."""
    task_name = action["task_name"]
    task_type = action["task_type"]
    segment_start, segment_end = action["start_frame"], action["end_frame"]
    sequence_fps = 5

    while True:
        frames = extract_frames_from_video(
            video_path,
            start_frame=segment_start,
            end_frame=segment_end,
            fps=sequence_fps,
        )
        num_images = len(frames)

        if num_images < 10:
            # Increase fps to the next higher option if below the minimum frame count
            current_index = FPS_OPTIONS.index(sequence_fps)
            if current_index < len(FPS_OPTIONS) - 1:
                sequence_fps = FPS_OPTIONS[current_index + 1]
            else:
                # If already at max fps and frames are still not enough, break the loop
                break
        elif num_images > 30:
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

    if task_type == "pick":
        timestep_prompt = LABEL_PICKUP_ACTION_HIGHER_FPS.format(
            action=task_name, object=action["object"]
        )
    else:
        timestep_prompt = LABEL_DEPOSIT_ACTION_HIGHER_FPS.format(
            action=task_name, object=action["object"]
        )

    response = await vlm_request(
        client, SYSTEM_PROMPT, timestep_prompt, frames, temperature=0, extract_json=True
    )

    start_image_number = response.get("start_image")
    end_image_number = response.get("end_image")

    if start_image_number is None or end_image_number is None:
        return None

    start_frame = segment_start + (start_image_number - 1) * video_fps / sequence_fps
    end_frame = segment_start + (end_image_number) * video_fps / sequence_fps

    result = {
        "task_name": task_name,
        "start_frame_of_segment": segment_start,
        "end_frame_of_segment": segment_end,
        "start_image": start_image_number,
        "end_image": end_image_number,
        "start_frame": start_frame,
        "end_frame": end_frame,
        "fps": sequence_fps,
        "task_type": task_type,
        "object": action["object"],
    }

    return result


async def relabel_episode_frames_with_higher_fps(labeled_timesteps):
    tasks_to_process = []
    for action in labeled_timesteps:
        tasks_to_process.append(
            relabel_action_frames_with_higher_fps(VIDEO_PATH, action, 30)
        )
    responses = await asyncio.gather(*tasks_to_process)
    filtered_responses = [response for response in responses if response is not None]
    return filtered_responses


async def adjust_frames_for_action(action):
    """Process a single robot task by calculating the range, getting frames, and analyzing the task."""
    task_name = action["task_name"]
    task_type = action["task_type"]
    object_name = action["object"]
    start_frame, end_frame = (
        action["modified_start_frame"],
        action["modified_end_frame"],
    )
    sequence_fps = 5  # Assuming a fixed FPS for extraction
    need_modification = action["need_modification"]

    if not need_modification:
        return action

    while need_modification:
        # Extract frames for analysis
        frames = extract_frames_from_video(
            VIDEO_PATH, start_frame=start_frame, end_frame=end_frame, fps=sequence_fps
        )

        # Determine prompts based on task type
        if task_type == "pick":
            start_prompt = REFINED_START_FRAME_PICK.format(
                action=task_name, object=object_name
            )
            end_prompt = REFINED_END_FRAME_PICK.format(
                action=task_name, object=object_name
            )
            start_check_prompt = CHECK_PICKUP_START_IMAGE_TIMING.format(
                action=task_name, object=object_name
            )
            end_check_prompt = CHECK_PICKUP_END_IMAGE_TIMING.format(
                action=task_name, object=object_name
            )
        elif task_type == "put":
            start_prompt = REFINED_START_FRAME_DEPOSIT.format(
                action=task_name, object=object_name
            )
            end_prompt = REFINED_END_FRAME_DEPOSIT.format(
                action=task_name, object=object_name
            )
            start_check_prompt = CHECK_DEPOSIT_START_IMAGE_TIMING.format(
                action=task_name, object=object_name
            )
            end_check_prompt = CHECK_DEPOSIT_END_IMAGE_TIMING.format(
                action=task_name, object=object_name
            )
        else:
            raise ValueError(f"Unsupported task type: {task_type}")

        if action["start_check"] != "perfect":
            start_frame = await vlm_request(
                client,
                SYSTEM_PROMPT,
                start_prompt,
                frames,
                temperature=0,
                extract_json=True,
            )
            action["modified_start_frame"] = start_frame.get("answer", "perfect")
            check_response = await vlm_request(
                client,
                SYSTEM_PROMPT,
                start_check_prompt,
                frames,
                temperature=0,
                extract_json=True,
            )
            action["start_check"] = check_response["answer"]

        if action["end_check"] != "perfect":
            end_frame = await vlm_request(
                client,
                SYSTEM_PROMPT,
                end_prompt,
                frames,
                temperature=0,
                extract_json=True,
            )
            action["modified_end_frame"] = end_frame.get("answer", "perfect")
            check_response = await vlm_request(
                client,
                SYSTEM_PROMPT,
                end_check_prompt,
                frames,
                temperature=0,
                extract_json=True,
            )
            action["end_check"] = check_response["answer"]

        # Re-evaluate need for modification
        action["need_modification"] = (
            action["start_check"] != "perfect" or action["end_check"] != "perfect"
        )

        return action


async def adjusting_frames_in_episode(tasks):
    adjusted_tasks = adjust_task_frames(tasks)

    tasks_to_process = [adjust_frames_for_action(action) for action in adjusted_tasks]
    responses = await asyncio.gather(*tasks_to_process)
    return responses
