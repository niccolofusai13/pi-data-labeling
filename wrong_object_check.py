import asyncio
from openai import AsyncOpenAI
import cv2

from video_labeling import extract_frames_from_video
from utils import extract_json_from_response

SYSTEM_PROMPT="""
**Comprehensive Video Task Analysis Framework**

**Environment and Components:**
- **Objects:**
  - Black Chopstick
  - Aluminum Takeout Container
  - Plastic Bowl
  - Orange Plate
  - Metal Spoon
  - Cardboard Food Container
  - Glass Bowl
- **Destinations:**
  - Transparent Plastic Box (on top of the black table)
  - Blue Trash Bin (next to the black table)
- **Robot Mechanism:**
  - Robot Arm equipped with a Gripper

**Task Definitions:**
- **Pick up OBJECT**: Recognized as complete when the robot's gripper has securely grasped the object, and it is fully suspended in the air with no contact with any surfaces.
- **Put OBJECT into DESTINATION**: Confirmed as complete when the object is inside the destination, and the gripper has retracted, fully releasing the object.

**Object Destination Rules:**
- Only the Aluminum Container and Cardboard Food Container go into the blue bin.
- The rest of the objects go into the clear plastic box on the table.
"""

WRONG_OBJECT_CHECK = """
### Analyze the Robot's Action: {action}

**Context:**
Your goal is to verify this action in the images is the same action as {action}.

**Description of the video:**
{description}

**Instruction:**
Please answer the following question? 
- Are more than half of the images showing a task other than {action} or using an object that isnt {object}? 

"""
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

async def check_wrong_task_episode(video_path, action, video_fps):
    """Process a single robot task by calculating the range, getting frames, and analyzing the task."""
    task_name = action["task_name"]
    task_type = action["task_type"]
    segment_start, segment_end = action['start_frame'], action['end_frame']
    sequence_fps = 5

        # Initial setup
    sequence_fps = 5
    
    frames = extract_frames_from_video(video_path, start_frame=segment_start, end_frame=segment_end, fps=sequence_fps)

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
                    WRONG_OBJECT_CHECK,
                ],
            },
        ],
        temperature=0,
    )

    response_content = response.choices[0].message.content
    print(f"task_name: {task_name}, response: {response_content}")
    extracted_response = extract_json_from_response(response_content)
    # print(extracted_response)

        
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
        "object": action["object"]
    }

    return result

async def check_wrong_task(video_path, labeled_timesteps):
    tasks_to_process = []
    for action in labeled_timesteps:
        tasks_to_process.append(
            check_wrong_task_episode(video_path, action, 30)
        )
    # Asynchronously process all tasks
    responses = await asyncio.gather(*tasks_to_process)
    return responses
