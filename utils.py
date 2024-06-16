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
    start_frame, video_fps, prev_section_fps, start_img, end_img, expansion_multiplier=2
):

    # Calculate the original start and end frames
    original_start = start_frame + (start_img - 1) * video_fps / prev_section_fps
    original_end = start_frame + (end_img * video_fps) /prev_section_fps

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
        for task in item['actions']['tasks']:
            # Extract the first word from the task description and convert it to lowercase
            first_word = task['task'].split()[0].lower()
            
            # Determine the type of task based on the first word, checked in lowercase for robustness
            if "pick" == first_word:
                task['task_type'] = 'pick'
            elif "put" == first_word:
                task['task_type'] = 'put'
            else:
                raise ValueError(f"Task description does not start with 'Pick' or 'Put': {task['task']}")
                
    return dataset


def calculate_new_frames(start_frame, end_frame, fps, steps=3, direction='negative'):
    window_size = 30 / fps  # Calculate window size based on the video FPS (30) and task FPS
    
    # Determine the sign based on the direction parameter
    sign = -1 if direction == 'negative' else 1
    
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

def adjust_frame(frame, fps, adjustment):
    """Adjust frame by a specific number of steps based on FPS and direction."""
    steps = 30 / fps * 3  # Calculate steps to move based on FPS
    if adjustment == "before":
        return max(0, frame - steps)  # Ensure frame does not go below 0
    elif adjustment == "after":
        return frame + steps
    else:
        return frame  # Return the original frame if the output is 'fine'
    

def adjust_task_frames(tasks):
    """
    Adjust the frame indices for a list of tasks based on 'start_check' and 'end_check'.
    It also sets modified start and end frames to provide a buffer around the adjusted frames.
    
    Args:
        tasks (list): List of task dictionaries.
    """
    for task in tasks:
        task['modified_start_frame'] = task['start_frame']
        task['modified_end_frame'] = task['end_frame']
        
        # Adjust the start_frame if needed
        if task['start_check'] != 'perfect':
            task['start_frame'] = adjust_frame(
                original_frame=task['start_frame'],
                fps=task['fps'],
                direction=task['start_check']
            )

            # Additional adjustment to create modified_start_frame
            task['modified_start_frame'] = adjust_frame(
                original_frame=task['start_frame'],
                fps=task['fps'],
                direction="late",  # Assuming "late" means to move back in time here
                steps=3
            )

            task['modified_end_frame'] = adjust_frame(
                original_frame=task['start_frame'],
                fps=task['fps'],
                direction="early",  # Assuming "early" means to move forward in time here
                steps=3
            )

        # Adjust the end_frame if needed
        if task['end_check'] != 'perfect':
            task['end_frame'] = adjust_frame(
                original_frame=task['end_frame'],
                fps=task['fps'],
                direction=task['end_check']
            )

            # Additional adjustment to create modified_end_frame
            task['modified_end_frame'] = adjust_frame(
                original_frame=task['end_frame'],
                fps=task['fps'],
                direction="early",  # Move forward in time
                steps=3
            )

            # Recalculate modified_start_frame for end adjustments to ensure consistency
            task['modified_start_frame'] = adjust_frame(
                original_frame=task['end_frame'],
                fps=task['fps'],
                direction="late",  # Move back in time
                steps=3
            )

    return tasks

