import cv2
from moviepy.editor import VideoFileClip
import time
import base64
import os
from openai import OpenAI
import re
import json

from IPython.display import Image, display, Audio, Markdown

import asyncio
from openai import AsyncOpenAI

from prompts import (
    DIFFERENCE_IN_IMAGES_SYSTEM_PROMPT,
    DIFFERENCE_IN_IMAGES_QUESTION,
    SYSTEM_PROMPT,
    QUESTION,
    TIMESTEP_PROMPT_TEMPLATE,
    PICK_UP_TIMESTEP_PROMPT_TEMPLATE,
    PUT_OBJECT_TIMESTEP_PROMPT_TEMPLATE,
    PICKUP_REFINE_PROMPT_TEMPLATE,
    DEPOSIT_REFINE_PROMPT_TEMPLATE,
    PICKUP_ZOOM_IN_PROMPT_TEMPLATE,
    DEPOSIT_ZOOM_IN_PROMPT_TEMPLATE,
    WRONG_OBJECT_CHECK,
    VIDEO_DESCRIPTION,
)

from before_after_prompts import (
    PICKUP_BEFORE_AFTER_END_PROMPT,
    PICKUP_BEFORE_AFTER_START_PROMPT,
    DEPOSIT_BEFORE_AFTER_END_PROMPT,
    DEPOSIT_BEFORE_AFTER_START_PROMPT,
    pick_up_end_label,
    pick_up_start_label,
    deposit_end_label,
    deposit_start_label
)
from utils import (
    extract_json_from_response,
    calculate_expanded_range,
    calculate_new_frames,
    check_response_for_before_after,
    adjust_frame
)

openai_api_key = "sk-proj-vq7xTCAdU9d2V0HKp55jT3BlbkFJBTOBsGNVO9ykIuxH5ZrJ"
client = AsyncOpenAI(api_key=openai_api_key)

MODEL = "gpt-4o"

# VIDEO_PATH = "observation_test.mp4"
# VIDEO_PATH = "blue_bowl_place.mp4"
VIDEO_PATH = "test2.mp4"
# VIDEO_PATH = "pi_test_2_short.mp4"
# VIDEO_PATH = "pi_test_2nd_half.mp4"
# VIDEO_PATH = "chopstick_video.mp4"

video = cv2.VideoCapture(VIDEO_PATH)
total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
video.release()
segment_size = 300


async def vlm_request(system_prompt, prompt, frames,temperature=0,extract_json=True):
    response = await client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
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
                    prompt,
                ],
            },
        ],
        temperature=temperature,
    )

    response = response.choices[0].message.content

    if extract_json:
        response = extract_json_from_response(response)

    return response


def add_task_type(dataset):
    for item in dataset:
        for task in item["actions"]["tasks"]:
            # Extract the first word from the task description and convert it to lowercase
            first_word = task["task"].split()[0].lower()

            # Determine the type of task based on the first word, checked in lowercase for robustness
            if "pick" == first_word:
                task["task_type"] = "pick"
            elif "put" == first_word:
                task["task_type"] = "put"
            else:
                raise ValueError(
                    f"Task description does not start with 'Pick' or 'Put': {task['task']}"
                )

    return dataset


def extract_frames_from_video(video_path, start_frame, end_frame, fps=10):
    base64Frames = []
    video = cv2.VideoCapture(video_path)
    video_fps = video.get(cv2.CAP_PROP_FPS)

    frames_to_skip = max(int(video_fps / fps), 1)
    curr_frame = start_frame

    while curr_frame < end_frame:
        video.set(cv2.CAP_PROP_POS_FRAMES, curr_frame)
        success, frame = video.read()
        if not success:
            break
        _, buffer = cv2.imencode(".jpg", frame)
        base64Frames.append(base64.b64encode(buffer).decode("utf-8"))
        curr_frame += frames_to_skip

    video.release()

    return base64Frames


async def process_frame_segment(
    start_frame, end_frame, system_prompt, user_prompt, include_images=True
):
    frames = extract_frames_from_video(VIDEO_PATH, start_frame, end_frame, fps=1)
    image_content = (
        [
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpg;base64,{x}", "detail": "high"},
            }
            for x in frames
        ]
        if include_images
        else []
    )
    response = await client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    (
                        "These are the 10 images from the video."
                        if include_images
                        else "Reviewing the following changes:"
                    ),
                    *image_content,
                    user_prompt,
                ],
            },
        ],
        temperature=0,
    )
    return response, frames  # Return frames if needed for further processing


async def label_moving_objects(frame_ranges):

    tasks = [
        process_frame_segment(
            start,
            end,
            DIFFERENCE_IN_IMAGES_SYSTEM_PROMPT,
            DIFFERENCE_IN_IMAGES_QUESTION,
        )
        for start, end in frame_ranges
    ]

    moved_objects_responses, moved_object_frames = zip(*await asyncio.gather(*tasks))

    moved_objects = [
        extract_json_from_response(response.choices[0].message.content)
        for response in moved_objects_responses
    ]

    return moved_objects, moved_object_frames


async def label_robot_actions(moved_objects, frame_ranges):

    # Prepare the second round of requests based on detected changes
    second_round_tasks = []
    for (start_frame, end_frame), change in zip(frame_ranges, moved_objects):
        print(change)
        if change:
            second_round_tasks.append(
                process_frame_segment(
                    start_frame,
                    end_frame,
                    SYSTEM_PROMPT,
                    QUESTION + json.dumps(change),
                    include_images=True,
                )
            )

    second_round_responses = await asyncio.gather(*second_round_tasks)
    print("done second round")
    actions = [
        extract_json_from_response(resp.choices[0].message.content)
        for resp, _ in second_round_responses
    ]

    # Combine actions with frame ranges
    actions_with_frame_ranges = [
        {"frame_range": f"{start}-{end}", "actions": action}
        for ((start, end), action) in zip(frame_ranges, actions)
    ]

    labeled_actions = add_task_type(actions_with_frame_ranges)

    return labeled_actions


async def label_video_timesteps(video_path, robot_actions):
    tasks_to_process = []
    for action_data in robot_actions:
        start_frame_of_segment = int(action_data["frame_range"].split("-")[0])
        for task in action_data["actions"]["tasks"]:
            tasks_to_process.append(
                label_episode_timesteps(video_path, task, 30, start_frame_of_segment)
            )
    # Asynchronously process all tasks
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
        timestep_prompt = PICKUP_REFINE_PROMPT_TEMPLATE.format(
            action=task_name, object=task["object"]
        )
    else:
        timestep_prompt = DEPOSIT_REFINE_PROMPT_TEMPLATE.format(
            action=task_name, object=task["object"]
        )

    # if task_type == 'pick':
    #     timestep_prompt = PICKUP_REFINE_PROMPT_TEMPLATE.format(
    #         action=task_name, num_images=num_images
    #     )
    # else:
    #     timestep_prompt = DEPOSIT_REFINE_PROMPT_TEMPLATE.format(
    #         action=task_name, num_images=num_images
    #     )

    # timestep_prompt = TIMESTEP_PROMPT_TEMPLATE.format(
    #     action=task_name, num_images=num_images
    # )
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


async def label_video_timesteps(video_path, robot_actions):
    tasks_to_process = []
    for action_data in robot_actions:
        start_frame_of_segment = int(action_data["frame_range"].split("-")[0])
        for task in action_data["actions"]["tasks"]:
            tasks_to_process.append(
                label_episode_timesteps(video_path, task, 30, start_frame_of_segment)
            )
    # Asynchronously process all tasks
    responses = await asyncio.gather(*tasks_to_process)
    return responses


async def zoom_episode_timesteps(video_path, action, video_fps):
    """Process a single robot task by calculating the range, getting frames, and analyzing the task."""
    task_name = action["task_name"]
    task_type = action["task_type"]
    segment_start, segment_end = action["start_frame"], action["end_frame"]
    sequence_fps = 5

    # Initial setup
    sequence_fps = 5
    fps_options = [3, 5, 10]  # Allowed fps values

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
        # print(f"task_name {task_name}, num_images: {num_images}")

        # Check number of images and adjust fps accordingly
        if num_images < 10:
            # Increase fps to the next higher option if below the minimum frame count
            current_index = fps_options.index(sequence_fps)
            if current_index < len(fps_options) - 1:
                sequence_fps = fps_options[current_index + 1]
            else:
                # If already at max fps and frames are still not enough, break the loop
                break
        elif num_images > 30:
            # Decrease fps to the next lower option if above the maximum frame count
            current_index = fps_options.index(sequence_fps)
            if current_index > 0:
                sequence_fps = fps_options[current_index - 1]
            else:
                # If already at minimum fps and frames are still too many, break the loop
                break
        else:
            # If the number of frames is within the acceptable range, break the loop
            break

    # Assign the prompt based on the task type
    if task_type == "pick":
        timestep_prompt = PICKUP_ZOOM_IN_PROMPT_TEMPLATE.format(
            action=task_name, object=action["object"]
        )
    else:
        timestep_prompt = DEPOSIT_ZOOM_IN_PROMPT_TEMPLATE.format(
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
    print(f"task_name: {task_name}, response: {response_content}")
    extracted_response = extract_json_from_response(response_content)
    # print(extracted_response)

    # need_more_info = check_response_for_before_after(extracted_response)
    # while need_more_info:
    #     print(action['task_name'])
    #     print(extracted_response)

    #     if need_more_info == 'before':
    #         action['start_frame'], action['end_frame'] = calculate_new_frames(action['start_frame'], action['end_frame'], sequence_fps, 3, direction='negative')
    #     elif need_more_info == 'after':
    #         action['start_frame'], action['end_frame'] = calculate_new_frames(action['start_frame'], action['end_frame'], sequence_fps, 3, direction='positive')
    #     else:
    #         raise ValueError("Unexpected value in need_more_info")

    #     frames = extract_frames_from_video(
    #         video_path, start_frame=action['start_frame'], end_frame=action['end_frame'], fps=sequence_fps
    #     )

    #     response = await client.chat.completions.create(
    #         model=MODEL,
    #         messages=[
    #             {"role": "system", "content": SYSTEM_PROMPT},
    #             {
    #                 "role": "user",
    #                 "content": [
    #                     "Reviewing the task with expanded frames.",
    #                     *map(
    #                         lambda x: {
    #                             "type": "image_url",
    #                             "image_url": {
    #                                 "url": f"data:image/jpg;base64,{x}",
    #                                 "detail": "high",
    #                             },
    #                         },
    #                         frames,
    #                     ),
    #                     timestep_prompt,
    #                 ],
    #             },
    #         ],
    #         temperature=0,
    #     )

    #     response_content = response.choices[0].message.content
    #     extracted_response = extract_json_from_response(response_content)
    #     print(f"extracted_response v2: {extracted_response}")
    #     need_more_info = check_response_for_before_after(extracted_response)

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


async def zoom_video_timesteps(video_path, labeled_timesteps):
    tasks_to_process = []
    for action in labeled_timesteps:
        tasks_to_process.append(zoom_episode_timesteps(video_path, action, 30))
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
        SYSTEM_PROMPT, VIDEO_DESCRIPTION, frames, extract_json=False
    )

    prompt = WRONG_OBJECT_CHECK.format(
        action=task_name, object=object, description=video_description
    )
    wrong_object_response = await vlm_request(
        SYSTEM_PROMPT, prompt, frames, extract_json=False
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


async def check_wrong_task(video_path, labeled_timesteps):
    tasks_to_process = []
    for action in labeled_timesteps:
        tasks_to_process.append(check_wrong_task_episode(video_path, action, 30))
    # Asynchronously process all tasks
    responses = await asyncio.gather(*tasks_to_process)
    return responses


async def episode_reflection(video_path, action, video_fps):
    """Process a single robot task by calculating the range, getting frames, and analyzing the task."""
    task_name = action["task_name"]
    task_type = action["task_type"]
    object = action["object"]
    start_frame, end_frame = action["start_frame"], action["end_frame"]
    sequence_fps = 5

    frames = extract_frames_from_video(
        video_path, start_frame=start_frame, end_frame=end_frame, fps=sequence_fps
    )

    if task_type == "pick":
        prompt = PICKUP_ZOOM_IN_PROMPT_TEMPLATE.format(
            action=task_name, object=action["object"]
        )
    else:
        prompt = DEPOSIT_ZOOM_IN_PROMPT_TEMPLATE.format(
            action=task_name, object=action["object"]
        )

    prompt = WRONG_OBJECT_CHECK.format(action=task_name, object=object)
    wrong_object_response = await vlm_request(
        SYSTEM_PROMPT, prompt, frames, extract_json=False
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

def adjust_fps_to_frame_count(video_path, segment_start, segment_end, initial_fps, min_frames, max_frames):
    """
    Adjust the frames per second (fps) to ensure the number of frames lies within a specified range.
    """
    sequence_fps = initial_fps
    fps_options = [3, 5, 10]
    while True:
        frames = extract_frames_from_video(
            video_path, start_frame=segment_start, end_frame=segment_end, fps=sequence_fps
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

    frames, fps = adjust_fps_to_frame_count(VIDEO_PATH, start_frame, end_frame, sequence_fps, 5, 20)
    
    print(task_name, fps, len(frames))
    # Determine prompts based on task type
    if task_type == "pick":
        start_prompt = PICKUP_BEFORE_AFTER_START_PROMPT.format(action=task_name, object=object_name)
        end_prompt = PICKUP_BEFORE_AFTER_END_PROMPT.format(action=task_name, object=object_name)
    elif task_type == "put":
        start_prompt = DEPOSIT_BEFORE_AFTER_START_PROMPT.format(action=task_name, object=object_name)
        end_prompt = DEPOSIT_BEFORE_AFTER_END_PROMPT.format(action=task_name, object=object_name)
    else:
        raise ValueError(f"Unsupported task type: {task_type}")

    
    # Request analysis for start and end frames
    start_response = await vlm_request(SYSTEM_PROMPT, start_prompt, frames, temperature=0, extract_json=False)
    end_response = await vlm_request(SYSTEM_PROMPT, end_prompt, frames, temperature=0, extract_json=False)

    start_check = extract_json_from_response(start_response)["answer"]
    end_check = extract_json_from_response(end_response)["answer"]


    action["start_answer"] = start_response
    action["end_answer"] = end_response 
    action['start_check'] = start_check
    action['end_check'] = end_check


    return action

async def reflection_step(video_path, tasks):
    tasks_to_process = [episode_reflection(video_path, action, 30) for action in tasks]
    responses = await asyncio.gather(*tasks_to_process)
    return responses

async def take_action(video_path, tasks):
    tasks_to_process = [episode_reflection(video_path, action, 30) for action in tasks]
    responses = await asyncio.gather(*tasks_to_process)
    return responses



async def main():

    frame_ranges = [
        (max(0, i - segment_size), min(total_frames, i))
        for i in range(segment_size, total_frames + segment_size, segment_size)
    ]

    moved_objects, _ = await label_moving_objects(frame_ranges)
    actions_with_frame_ranges = await label_robot_actions(moved_objects, frame_ranges)
    print(f"actions_with_frame_ranges: {actions_with_frame_ranges}")
    labeled_timesteps = await label_video_timesteps(
        VIDEO_PATH, actions_with_frame_ranges
    )
    zoomed_results_test = await zoom_video_timesteps(VIDEO_PATH, labeled_timesteps)
    wrong_results_test = await check_wrong_task(VIDEO_PATH, zoomed_results_test)
    filtered_tasks_test = [task for task in wrong_results_test if task['wrong_object'] != 'Yes']
    new_tasks_test = await reflection_step(VIDEO_PATH, filtered_tasks_test)


    print(f"labeled_timesteps are: {labeled_timesteps}")

    # print("Changes Detected:", changes_detected)
    # print("Robot Actions:", robot_actions)
    # print("Final Responses:", final_responses)


if __name__ == "__main__":
    asyncio.run(main())
