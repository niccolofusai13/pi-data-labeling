import json
import re


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
    start_frame, video_fps, desired_fps, start_img, end_img, expansion_multiplier=2
):

    # Calculate the original start and end frames
    original_start = start_frame + (start_img - 1) * video_fps / desired_fps
    original_end = start_frame + (end_img * video_fps) /desired_fps

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