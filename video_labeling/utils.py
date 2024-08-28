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
            print(response)
            return None
    except Exception as e:
        print(f"Error decoding JSON or accessing response: {e}")
        return None


def calculate_expanded_range(start_frame, end_frame, buffer_multiplier=2):
    expanded_start = max(
        0, start_frame - buffer_multiplier * 30
    )  # this is actually number of seconds - easier imo to count like that
    expanded_end = (
        end_frame + buffer_multiplier * 30
    )  # this is actually number of seconds - easier imo to count like that
    return expanded_start, expanded_end


def check_response_for_before_after(response):
    if "before" in response.values():
        return "before"
    if "after" in response.values():
        return "after"
    return None


def create_smaller_frame_window_from_checks(action):
    """
    Adjust the frame indices for a list of tasks based on 'start_check' and 'end_check'.
    It sets modified start and end frames to provide a buffer around the adjusted frames.
    """

    action["need_modification"] = (
        action["start_check"] != "perfect" or action["end_check"] != "perfect"
    )
    action["modified_start_start_frame"] = action["start_frame"]
    action["modified_end_end_frame"] = action["end_frame"]

    if action["start_check"] != "perfect":  # only options here are 'early' and 'late'
        backward_seconds = 2 if action["start_check"] == "late" else 1
        forward_seconds = 1 if action["start_check"] == "late" else 2

        action["modified_start_start_frame"] = adjust_frame_indices(
            action["start_frame"], "backward", backward_seconds
        )
        action["modified_start_end_frame"] = adjust_frame_indices(
            action["start_frame"], "forward", forward_seconds
        )

    if action["end_check"] != "perfect":  # only options here are 'early' and 'late'
        backward_seconds = 2 if action["end_check"] == "late" else 1
        forward_seconds = 1 if action["end_check"] == "late" else 2

        action["modified_end_start_frame"] = adjust_frame_indices(
            action["end_frame"], "backward", backward_seconds
        )
        action["modified_end_end_frame"] = adjust_frame_indices(
            action["end_frame"], "forward", forward_seconds
        )

    return action


def adjust_task_frames(tasks):
    """
    Adjust the frame indices for a list of tasks based on 'start_check' and 'end_check'.
    It sets modified start and end frames to provide a buffer around the adjusted frames.
    """
    for task in tasks:

        task["need_modification"] = (
            task["start_check"] != "perfect" or task["end_check"] != "perfect"
        )
        task["modified_start_start_frame"] = task["start_frame"]
        task["modified_end_end_frame"] = task["end_frame"]

        if task["start_check"] != "perfect":
            # Adjust start and end frames based on the evaluation of the start condition
            backward_seconds = 2 if task["start_check"] == "late" else 1
            forward_seconds = 1 if task["start_check"] == "late" else 2

            task["modified_start_start_frame"] = adjust_frame_indices(
                task["start_frame"], "backward", backward_seconds
            )
            task["modified_start_end_frame"] = adjust_frame_indices(
                task["start_frame"], "forward", forward_seconds
            )

        if task["end_check"] != "perfect":
            # Adjust start and end frames based on the evaluation of the end condition
            backward_seconds = 2 if task["end_check"] == "late" else 1
            forward_seconds = 1 if task["end_check"] == "late" else 2

            task["modified_end_start_frame"] = adjust_frame_indices(
                task["end_frame"], "backward", backward_seconds
            )
            task["modified_end_end_frame"] = adjust_frame_indices(
                task["end_frame"], "forward", forward_seconds
            )

    return tasks


def adjust_frame_indices(original_frame, direction, num_seconds=1):
    """adjusting the frame to be"""
    # there's 30 fps in these videos
    adjustment = 30 * num_seconds
    if direction == "backward":
        return max(0, original_frame - adjustment)
    elif direction == "forward":
        return original_frame + adjustment
    else:
        return original_frame


async def vlm_request(
    client, system_prompt, prompt, frames, temperature=0, extract_json=True
):

    messages = [
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
    ]

    response = await client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=temperature,
    )

    response = response.choices[0].message.content

    if extract_json:
        response = extract_json_from_response(response)

    return response


def adjust_fps_to_frame_count(
    video_path, segment_start, segment_end, initial_fps, min_frames, max_frames
):
    """
    Adjust the frames per second (fps) to ensure the number of frames lies within a specified range.
    """
    sequence_fps = initial_fps
    fps_options = [1,2,3, 5, 10]
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
