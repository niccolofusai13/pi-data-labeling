import cv2
import json
import asyncio
from openai import AsyncOpenAI
import os

from config import (
    OPENAI_API_KEY,
    MODEL,
    VIDEO_PATH,
    FRAMES_SEGMENT_SIZE,
    FPS_OPTIONS,
    RESULTS_OUTPUT_PATH,
)
from video_labeling.utils import extract_frames_from_video
from video_labeling.prompts.shared import SYSTEM_PROMPT
from video_labeling.prompts.find_objects import (
    FIND_OBJECTS_SYSTEM_PROMPT,
    FIND_OBJECTS,
)
from video_labeling.prompts.label_actions import LABEL_ACTIONS
from video_labeling.prompts.label_frames import (
    LABEL_PICKUP_ACTION,
    LABEL_DEPOSIT_ACTION,
    LABEL_PICKUP_ACTION_HIGHER_FPS,
    LABEL_DEPOSIT_ACTION_HIGHER_FPS,
    REFINED_START_FRAME_PICK,
    REFINED_END_FRAME_PICK,
    REFINED_START_FRAME_DEPOSIT,
    REFINED_END_FRAME_DEPOSIT
)
from video_labeling.prompts.reflection_checks import (
    VIDEO_DESCRIPTION,
    CHECK_WRONG_ACTION,
    CHECK_PICKUP_START_IMAGE_TIMING,
    CHECK_PICKUP_END_IMAGE_TIMING,
    CHECK_DEPOSIT_START_IMAGE_TIMING,
    CHECK_DEPOSIT_END_IMAGE_TIMING,
)

from video_labeling.utils import (
    extract_json_from_response,
    calculate_expanded_range,
    adjust_task_frames,
    vlm_request,
    add_task_type,
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


async def label_actions(moved_objects):
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


async def label_frame_range(robot_actions):
    tasks_to_process = []
    for action_data in robot_actions:
        start_frame_of_segment = int(action_data["frame_range"].split("-")[0])
        for task in action_data["actions"]["tasks"]:
            tasks_to_process.append(
                label_episode_timesteps(VIDEO_PATH, task, 30, start_frame_of_segment)
            )

    responses = await asyncio.gather(*tasks_to_process)
    return responses


async def label_episode_timesteps(video_path, task, video_fps, start_frame_of_segment):
    """Process a single robot task by calculating the range, getting frames, and analyzing the task."""
    task_name = task["task"]
    image_range = task["image_range"]
    task_type = task["task_type"]
    start_img, end_img = map(int, image_range.split("-"))
    sequence_fps = 3
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

    while True:  # Loop until the number of images is less than 15

        # Calculate expanded frame range based on image_range
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

    response = await client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    "Reviewing the task with expanded frames.",
                    *map(
                        lambda x: {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpg;base64,{x}",
                                "detail": "high",
                            },
                        },
                        frames,
                    ),
                    timestep_prompt,
                ],
            },
        ],
        temperature=0,
    )

    response_content = response.choices[0].message.content
    extracted_data = extract_json_from_response(response_content)
    start_frame = (
        expanded_start
        + (extracted_data.get("start_image") - 1) * video_fps / sequence_fps
    )
    end_frame = (
        expanded_start + (extracted_data.get("end_image")) * video_fps / sequence_fps
    )

    result = {
        "task_name": task_name,
        "start_frame_of_segment": expanded_start,
        "end_frame_of_segment": expanded_end,
        "start_image": extracted_data.get("start_image"),
        "end_image": extracted_data.get("end_image"),
        "start_frame": start_frame,
        "end_frame": end_frame,
        "fps": sequence_fps,
        "task_type": task_type,
        "object": task["object"],
    }

    return result


async def zoom_episode_timesteps(video_path, action, video_fps):
    """Process a single robot task by calculating the range, getting frames, and analyzing the task."""
    task_name = action["task_name"]
    task_type = action["task_type"]
    segment_start, segment_end = action["start_frame"], action["end_frame"]
    sequence_fps = 5

    # Initial setup
    sequence_fps = 5

    while True:
        # print(f"task_name {task_name}, fps: {sequence_fps}")
        # Extract frames with the current fps setting
        frames = extract_frames_from_video(
            video_path,
            start_frame=segment_start,
            end_frame=segment_end,
            fps=sequence_fps,
        )
        num_images = len(frames)

        # Check number of images and adjust fps accordingly
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

    # Assign the prompt based on the task type
    if task_type == "pick":
        timestep_prompt = LABEL_PICKUP_ACTION_HIGHER_FPS.format(
            action=task_name, object=action["object"]
        )
    else:
        timestep_prompt = LABEL_DEPOSIT_ACTION_HIGHER_FPS.format(
            action=task_name, object=action["object"]
        )

    response = await client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    "These are a sequence of images from the video. The first image is the start image, and the final image is the end image.",
                    *map(
                        lambda x: {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpg;base64,{x}",
                                "detail": "high",
                            },
                        },
                        frames,
                    ),
                    timestep_prompt,
                ],
            },
        ],
        temperature=0,
    )

    response_content = response.choices[0].message.content
    extracted_response = extract_json_from_response(response_content)

    start_frame = (
        segment_start
        + (extracted_response.get("start_image") - 1) * video_fps / sequence_fps
    )
    end_frame = (
        segment_start + (extracted_response.get("end_image")) * video_fps / sequence_fps
    )

    result = {
        "task_name": task_name,
        "start_frame_of_segment": segment_start,
        "end_frame_of_segment": segment_end,
        "start_image": extracted_response.get("start_image"),
        "end_image": extracted_response.get("end_image"),
        "start_frame": start_frame,
        "end_frame": end_frame,
        "fps": sequence_fps,
        "task_type": task_type,
        "object": action["object"],
    }

    return result


async def relabel_frames_with_higher_fps(labeled_timesteps):
    tasks_to_process = []
    for action in labeled_timesteps:
        tasks_to_process.append(zoom_episode_timesteps(VIDEO_PATH, action, 30))
    # Asynchronously process all tasks
    responses = await asyncio.gather(*tasks_to_process)
    return responses


async def check_wrong_task_episode(video_path, action, video_fps):
    """Process a single robot task by calculating the range, getting frames, and analyzing the task."""
    task_name = action["task_name"]
    task_type = action["task_type"]
    object = action["object"]
    start_frame, end_frame = action["start_frame"], action["end_frame"]
    sequence_fps = 5

    frames = extract_frames_from_video(
        video_path, start_frame=start_frame, end_frame=end_frame, fps=sequence_fps
    )

    video_description = await vlm_request(
        client, SYSTEM_PROMPT, VIDEO_DESCRIPTION, frames, extract_json=False
    )

    prompt = CHECK_WRONG_ACTION.format(
        action=task_name, object=object, description=video_description
    )
    wrong_object_response = await vlm_request(
        client, SYSTEM_PROMPT, prompt, frames, extract_json=False
    )

    result = {
        "task_name": task_name,
        "start_frame": start_frame,
        "end_frame": end_frame,
        "fps": sequence_fps,
        "task_type": task_type,
        "object": action["object"],
        "wrong_object": wrong_object_response,
    }

    return result


async def remove_erroneous_episodes(labeled_timesteps):
    tasks_to_process = []
    for action in labeled_timesteps:
        tasks_to_process.append(check_wrong_task_episode(VIDEO_PATH, action, 30))
    # Asynchronously process all tasks
    responses = await asyncio.gather(*tasks_to_process)
    filtered_tasks_test = [task for task in responses if task["wrong_object"] != "Yes"]

    return filtered_tasks_test


def adjust_fps_to_frame_count(
    video_path, segment_start, segment_end, initial_fps, min_frames, max_frames
):
    """
    Adjust the frames per second (fps) to ensure the number of frames lies within a specified range.
    """
    sequence_fps = initial_fps
    fps_options = [3, 5, 10]
    while True:
        frames = extract_frames_from_video(
            video_path,
            start_frame=segment_start,
            end_frame=segment_end,
            fps=sequence_fps,
        )
        num_images = len(frames)

        if num_images < min_frames:
            # Increase fps to the next higher option if below the minimum frame count
            current_index = fps_options.index(sequence_fps)
            if current_index < len(fps_options) - 1:
                sequence_fps = fps_options[current_index + 1]
            else:
                # If already at max fps and frames are still not enough, use the highest possible fps
                break
        elif num_images > max_frames:
            # Decrease fps to the next lower option if above the maximum frame count
            current_index = fps_options.index(sequence_fps)
            if current_index > 0:
                sequence_fps = fps_options[current_index - 1]
            else:
                # If already at minimum fps and frames are still too many, use the lowest possible fps
                break
        else:
            # If the number of frames is within the acceptable range, stop adjusting
            break

    return frames, sequence_fps


async def episode_reflection(video_path, action, video_fps):
    """Process a single robot task by calculating the range, getting frames, and analyzing the task."""
    task_name = action["task_name"]
    task_type = action["task_type"]
    object_name = action["object"]
    start_frame, end_frame = action["start_frame"], action["end_frame"]
    sequence_fps = 5  # Assuming a fixed FPS for extraction

    # # Extract frames for analysis
    # frames = extract_frames_from_video(
    #     video_path, start_frame=start_frame, end_frame=end_frame, fps=sequence_fps
    # )

    frames, fps = adjust_fps_to_frame_count(
        VIDEO_PATH, start_frame, end_frame, sequence_fps, 5, 20
    )

    # Determine prompts based on task type
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

    # Request analysis for start and end frames
    start_response = await vlm_request(
        client, SYSTEM_PROMPT, start_prompt, frames, temperature=0, extract_json=False
    )
    end_response = await vlm_request(
        client, SYSTEM_PROMPT, end_prompt, frames, temperature=0, extract_json=False
    )

    start_check = extract_json_from_response(start_response)["answer"]
    end_check = extract_json_from_response(end_response)["answer"]

    action["start_answer"] = start_response
    action["end_answer"] = end_response
    action["start_check"] = start_check
    action["end_check"] = end_check

    return action


async def run_checks(tasks):
    tasks_to_process = [episode_reflection(VIDEO_PATH, action, 30) for action in tasks]
    responses = await asyncio.gather(*tasks_to_process)
    return responses


async def episode_double_click(action):
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


async def refine_labels(tasks):
    adjusted_tasks = adjust_task_frames(tasks)

    tasks_to_process = [episode_double_click(action) for action in adjusted_tasks]
    responses = await asyncio.gather(*tasks_to_process)
    return responses


async def label_video():

    print(f"Step 1: Identifying which objects have moved...")
    moved_objects = await identify_moved_objects()

    print(f"Step 2: Identifying which actions have taken place...")
    labeled_actions = await label_actions(moved_objects)

    labeled_frames = await label_frame_range(labeled_actions)
    print(f"Step 3: Labeling the frame range...")
    higher_fps_labeled_frames = await relabel_frames_with_higher_fps(labeled_frames)

    print(f"Step 4: Removing erroneos episodes...")
    qa_labels = await remove_erroneous_episodes(higher_fps_labeled_frames)

    print(f"Step 5: Running checks...")
    checks_feedback = await run_checks(qa_labels)

    print(f"Step 6: Iteratively refining labels until all checks pass...")
    final_results = await refine_labels(checks_feedback)

    print(f"Step 7: Done... saving results...")
    output_file_path = os.path.join(RESULTS_OUTPUT_PATH, "test_results.json")
    with open(output_file_path, "w") as file:
        json.dump(final_results, file, indent=4)


if __name__ == "__main__":
    asyncio.run(label_video())
