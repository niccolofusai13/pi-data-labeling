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
)
from utils import extract_json_from_response, calculate_expanded_range

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

def extract_frames_from_video(video_path, start_frame, end_frame, seconds_per_frame=0.5):
    base64Frames = []
    video = cv2.VideoCapture(video_path)
    fps = video.get(cv2.CAP_PROP_FPS)
    frames_to_skip = int(fps * seconds_per_frame)
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
    frames = extract_frames_from_video(VIDEO_PATH, start_frame, end_frame, seconds_per_frame=1)
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

    moved_objects_responses, moved_object_frames = zip(
        *await asyncio.gather(*tasks)
    )

    moved_objects = [
        extract_json_from_response(response.choices[0].message.content)
        for response in moved_objects_responses
    ]

    return moved_objects, moved_object_frames

async def label_robot_actions(moved_objects, frame_ranges):
    
    # Prepare the second round of requests based on detected changes
    second_round_tasks = []
    for (start_frame, end_frame), change in zip(frame_ranges, moved_objects):
        if change:
            second_round_tasks.append(
                process_frame_segment(
                    start_frame,
                    end_frame,
                    SYSTEM_PROMPT,
                    QUESTION + json.dumps(change),
                    include_images=True
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
    return actions_with_frame_ranges
    

async def label_episode_timesteps(video_path, task, frames_to_skip, start_frame_of_segment):
    task_name = task['task']
    image_range = task['image_range']
    
    start_img, end_img = map(int, image_range.split('-'))

    # Calculate expanded range
    expanded_start, expanded_end = calculate_expanded_range(start_frame_of_segment, frames_to_skip, start_img, end_img, expansion_multiplier=2)

    # Extract frames
    frames = extract_frames_from_video(video_path, expanded_start, expanded_end, seconds_per_frame=1)

    # Prepare prompt
    timestep_prompt = TIMESTEP_PROMPT_TEMPLATE.format(task_name=task_name)

    # Prepare API call
    response = await client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": [
                "Reviewing the task with expanded frames.",
                *map(lambda x: {"type": "image_url", "image_url": {"url": f'data:image/jpg;base64,{x}', "detail": "high"}}, frames),
                timestep_prompt
            ]}
        ],
        temperature=0,
    )
    return response

async def label_video_timesteps(video_path, robot_actions):
    tasks_to_process = []
    for action_data in robot_actions:
        start_frame_of_segment = int(action_data['frame_range'].split('-')[0])
        for task in action_data['actions']['tasks']:
            tasks_to_process.append(label_episode_timesteps(video_path, task, 30, start_frame_of_segment))  # Assuming 30 as frames_to_skip
    # Asynchronously process all tasks
    responses = await asyncio.gather(*tasks_to_process)
    return responses


async def label_episode_timesteps(video_path, task, frames_to_skip, start_frame_of_segment):
    """Process a single robot task by calculating the range, getting frames, and analyzing the task."""
    task_name = task['task']
    image_range = task['image_range']
    start_img, end_img = map(int, image_range.split('-'))

    # Calculate expanded frame range based on image_range
    expanded_start, expanded_end = calculate_expanded_range(start_frame_of_segment, frames_to_skip, start_img, end_img, expansion_multiplier=2)
    frames = extract_frames_from_video(video_path, seconds_per_frame=0.5, start_frame=expanded_start, end_frame=expanded_end)
    num_images = len(frames)
    timestep_prompt = TIMESTEP_PROMPT_TEMPLATE.format(action=task_name, num_images=num_images)
    response = await client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": [
                "Reviewing the task with expanded frames.",
                *map(lambda x: {"type": "image_url", "image_url": {"url": f'data:image/jpg;base64,{x}', "detail": "high"}}, frames),
                timestep_prompt
            ]}
        ],
        temperature=0,
    )

    response_content = response.choices[0].message.content
    extracted_data = extract_json_from_response(response_content)
    start_frame = expanded_start + (extracted_data.get("start_image") - 1) * frames_to_skip
    end_frame = expanded_start + (extracted_data.get("end_image") - 1) * frames_to_skip

    result = {
            "task_name": task_name,
            "start_frame_of_segment": expanded_start,
            "end_frame_of_segment": expanded_end,
            "start_image": extracted_data.get("start_image"),
            "end_image": extracted_data.get("end_image"), 
            "start_frame":start_frame,
            "end_frame":end_frame,
            "frames_to_skip": frames_to_skip #this should go outside of this dict since its repeated. # TODO
        }

    return result


async def label_video_timesteps(video_path, robot_actions):
    tasks_to_process = []
    for action_data in robot_actions:
        start_frame_of_segment = int(action_data['frame_range'].split('-')[0])
        for task in action_data['actions']['tasks']:
            tasks_to_process.append(label_episode_timesteps(video_path, task, 30, start_frame_of_segment))  # Assuming 30 as frames_to_skip
    # Asynchronously process all tasks
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
    labeled_timesteps = await label_video_timesteps(VIDEO_PATH, actions_with_frame_ranges)
    print(f"labeled_timesteps are: {labeled_timesteps}")
    # # Replace 'VIDEO_PATH' with your actual video file path
    # changes_detected, robot_actions = await annotate_video(VIDEO_PATH)
    # final_responses = await annotate_video_with_timesteps(VIDEO_PATH, robot_actions)
    # print("Changes Detected:", changes_detected)
    # print("Robot Actions:", robot_actions)
    # print("Final Responses:", final_responses)

if __name__ == "__main__":
    asyncio.run(main())
    