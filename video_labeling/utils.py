import json
import re
import cv2
import base64
from config import MODEL


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


def extract_json_from_response(response):
    try:
        match = re.search(r"\{.*\}", response, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        else:
            print("No JSON object found in the response")
            return None
    except Exception as e:
        print(f"Error decoding JSON or accessing response: {e}")
        return None


def calculate_expanded_range(
    start_frame, video_fps, prev_section_fps, start_img, end_img, expansion_multiplier=2
):

    # Calculate the original start and end frames
    original_start = start_frame + (start_img - 1) * video_fps / prev_section_fps
    original_end = start_frame + (end_img * video_fps) / prev_section_fps

    # Compute original window size in frames
    original_window_size = original_end - original_start

    # Calculate the expanded window size using the multiplier
    expanded_window_size = original_window_size * expansion_multiplier

    # Calculate the additional buffer needed on each side
    buffer = (expanded_window_size - original_window_size) // 2

    # Calculate the new start and end frames with additional buffer
    new_start = max(0, original_start - buffer)
    new_end = original_end + buffer

    return new_start, new_end


def convert_frame_number_to_timestamp(current_frame_num, fps=30):
    """
    Convert a given frame number to a timestamp in MM:SS.t format, rounded to the nearest tenth of a second.
    """
    # Calculate the total number of seconds for the current frame
    total_seconds = current_frame_num / fps

    # Calculate minutes and seconds
    minutes = int(total_seconds // 60)
    seconds = total_seconds % 60

    # Round seconds to the nearest tenth
    seconds = round(seconds, 1)

    # Format the timestamp as MM:SS.t
    timestamp = f"{minutes:02}:{seconds:04.1f}"

    return timestamp


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


def calculate_new_frames(start_frame, end_frame, fps, steps=3, direction="negative"):
    window_size = (
        30 / fps
    )  # Calculate window size based on the video FPS (30) and task FPS

    # Determine the sign based on the direction parameter
    sign = -1 if direction == "negative" else 1

    # Adjust start_frame and end_frame based on the direction and steps
    new_start_frame = max(0, start_frame + sign * steps * window_size)
    new_end_frame = max(0, end_frame + sign * steps * window_size)

    return new_start_frame, new_end_frame


def check_response_for_before_after(response):
    if "before" in response.values():
        return "before"
    if "after" in response.values():
        return "after"
    return None


def adjust_task_frames(tasks):
    """
    Adjust the frame indices for a list of tasks based on 'start_check' and 'end_check'.
    It also sets modified start and end frames to provide a buffer around the adjusted frames.

    Args:
        tasks (list): List of task dictionaries.
    """
    # Check if the task needs modification
    for task in tasks:
        task["need_modification"] = (
            task["start_check"] != "perfect" or task["end_check"] != "perfect"
        )
        task["modified_start_frame"] = task["start_frame"]
        task["modified_end_frame"] = task["end_frame"]

        # Adjust the start_frame if needed
        if task["start_check"] != "perfect":
            task["modified_start_frame"] = adjust_frame(
                original_frame=task["modified_start_frame"],
                fps=task["fps"],
                direction=task["start_check"],
            )

            # Additional adjustment to create modified_start_frame
            task["modified_start_frame"] = adjust_frame(
                original_frame=task["modified_start_frame"],
                fps=task["fps"],
                direction="late",  # Assuming "late" means to move back in time here
                steps=3,
            )

            task["modified_end_frame"] = adjust_frame(
                original_frame=task["modified_start_frame"],
                fps=task["fps"],
                direction="early",  # Assuming "early" means to move forward in time here
                steps=3,
            )

        # Adjust the end_frame if needed
        if task["end_check"] != "perfect":
            task["modified_end_frame"] = adjust_frame(
                original_frame=task["modified_end_frame"],
                fps=task["fps"],
                direction=task["end_check"],
            )

            # Additional adjustment to create modified_end_frame
            task["modified_end_frame"] = adjust_frame(
                original_frame=task["modified_end_frame"],
                fps=task["fps"],
                direction="early",  # Move forward in time
                steps=3,
            )

            # Recalculate modified_start_frame for end adjustments to ensure consistency
            task["modified_start_frame"] = adjust_frame(
                original_frame=task["modified_end_frame"],
                fps=task["fps"],
                direction="late",  # Move back in time
                steps=3,
            )

    return tasks


def adjust_frame(original_frame, fps, direction, steps=5):
    adjustment = (30 / fps) * steps
    if direction == "early":
        return max(0, original_frame + adjustment)
    elif direction == "late":
        return original_frame - adjustment
    else:
        return original_frame


async def vlm_request(
    client, system_prompt, prompt, frames, temperature=0, extract_json=True
):
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
