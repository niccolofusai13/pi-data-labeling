import asyncio
import copy

from video_labeling.utils import extract_frames_from_video
from video_labeling.prompts.shared import SYSTEM_PROMPT
from video_labeling.prompts.label_frames import REFINED_START_FRAME_PICK
from video_labeling.prompts.reflection_checks import (
    CHECK_PICKUP_START_IMAGE_TIMING,
    CHECK_PICKUP_END_IMAGE_TIMING,
    CHECK_DEPOSIT_START_IMAGE_TIMING,
    CHECK_DEPOSIT_END_IMAGE_TIMING,
)

from video_labeling.utils import (
    vlm_request,
    extract_json_from_response,
    adjust_fps_to_frame_count,
)


def create_check_prompts(task_type, task_name, object_name):
    """Creating the prompt template to run the checks"""
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
    return start_prompt, end_prompt


async def check_action_frame_number_labels(action, client, video_path, fps=5):
    """Check timing"""
    # start_frame, end_frame = action["start_frame"], action["end_frame"]
    # if action['action'] == 'Pick up Aluminum Container': 
    #     print(action["start_frame"])
    frames, _ = adjust_fps_to_frame_count(
        video_path, action["start_frame"], action["end_frame"], fps, 5, 20
    )


    start_prompt, end_prompt = create_check_prompts(
        action["action_type"], action["action"], action["object"]
    )
    start_response = await vlm_request(
        client, SYSTEM_PROMPT, start_prompt, frames, extract_json=False
    )
    end_response = await vlm_request(
        client, SYSTEM_PROMPT, end_prompt, frames, extract_json=False
    )

    # start_check = extract_json_from_response(start_response)["answer"]
    # counter = 0
    # while start_check == "wrong_object" and counter <= 3: 
    #     action["start_frame"] += 30

    #     frames, _ = adjust_fps_to_frame_count(
    #         video_path, action["start_frame"], action["end_frame"], fps, 5, 20
    #     )

    #     start_check = await vlm_request(
    #         client, SYSTEM_PROMPT, start_prompt, frames, extract_json=True
    #     )

    #     print(f"the action is: {action['action']} and the check is: {start_check} after round {counter + 1}")
    #     print(action["start_frame"])
    #     ### ISSUE IS AFTER YOU DO +- so it goes back !!
    #     counter += 1


    action.update(
        {
            # "start_frame": action["start_frame"],
            "start_answer": start_response,
            "end_answer": end_response,
            "start_check": extract_json_from_response(start_response)["answer"],
            "end_check": extract_json_from_response(end_response)["answer"],
        }
    )

    return action


async def check_episode_frame_number_labels(client, video_path, labeled_actions, fps=5):
    tasks_to_process = [
        check_action_frame_number_labels(
            copy.deepcopy(action), client, video_path, fps=fps
        )
        for action in labeled_actions
    ]
    responses = await asyncio.gather(*tasks_to_process)
    return responses



# async def determine_wrong_pickup_start_action(action, client, video_path, fps=5):
#     """Determining if an action doesn't match the description label"""

#     if action["action_type"]=="put": 
#         return action

#     print(f"original start frame for {action['action']} was {action['start_frame']}")
#     moved_start_frame = action['start_frame'] + 30 # a second
#     # moved_end_frame = moved_start_frame + 30 # a second after that

#     frames = extract_frames_from_video(video_path, moved_start_frame, action['end_frame'], fps=fps)

#     prompt = CHECK_WRONG_ACTION.format(
#         object=action["object"],
#     )

#     wrong_object_response = await vlm_request(
#         client, SYSTEM_PROMPT, prompt, frames, extract_json=True
#     )

#     check = wrong_object_response['answer']
#     print(f"{action['action']} is {check}")

#     if check != "perfect": 
#         print(f"{action['action']} is APPARENTLY BAD")        
#         action["start_frame"] += 45 # a second and a half

#         frames = extract_frames_from_video(
#                 video_path, start_frame=action["start_frame"], end_frame=action["end_frame"], fps=fps
#             )
        
        
#         refined_frame_label_prompt = REFINED_START_FRAME_PICK.format(
#                 action=action["action"], object=action["object"]
#             )
        
#         start_frame_answer = await vlm_request(
#                 client,
#                 SYSTEM_PROMPT,
#                 refined_frame_label_prompt,
#                 frames,
#                 temperature=0,
#                 extract_json=True,
#             )
        
#         if start_frame_answer is None: 
#             return action
#         start_image_number = start_frame_answer.get("answer")
#         if start_image_number is None: 
#             return action
        
#         action["start_frame"] += (start_image_number - 1) * 30 / fps

#     print(f"adjusted start frame for {action['action']} is {action['start_frame']}")

#     return action


# async def adjust_wrong_pickup_start_labels(client, video_path, labeled_timesteps, fps=5):
#     """Getting rid of all erroneous actions in an episode"""

#     tasks_to_process = [
#         determine_wrong_pickup_start_action(copy.deepcopy(action), client, video_path, fps=fps)
#         for action in labeled_timesteps
#     ]
#     responses = await asyncio.gather(*tasks_to_process)
#     return responses

