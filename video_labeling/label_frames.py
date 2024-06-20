import asyncio
import copy

from config import FPS_OPTIONS
from video_labeling.utils import extract_frames_from_video
from video_labeling.prompts.shared import SYSTEM_PROMPT
from video_labeling.prompts.label_frames import (
    REFINED_START_FRAME_PICK,
    REFINED_END_FRAME_PICK,
    REFINED_START_FRAME_DEPOSIT,
    REFINED_END_FRAME_DEPOSIT,
    LABEL_PICKUP_ACTION,
    LABEL_DEPOSIT_ACTION
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
    adjust_frame_indices, 
    adjust_fps_to_frame_count, 
    adjust_task_frame
)


async def label_episode_frame_ranges(client, video_path, labeled_actions, fps=5):
    tasks_to_process = []
    for action in labeled_actions:
        tasks_to_process.append(
            label_action_frame_range(client, video_path, copy.deepcopy(action), fps)
        )

    responses = await asyncio.gather(*tasks_to_process)
    filtered_responses = [response for response in responses if response is not None]

    return filtered_responses


async def label_action_frame_range(client, video_path, action_dict, fps):
    """Process a single robot task by calculating the range, getting frames, and analyzing the task."""
    video_fps = 30
    buffer_multiplier = 2

    expanded_start, expanded_end = calculate_expanded_range(action_dict['start_frame'], action_dict['end_frame'], buffer_multiplier=buffer_multiplier)
    
    frames = extract_frames_from_video(
        video_path, start_frame=expanded_start, end_frame=expanded_end, fps=fps
    )
    

    # We want to make sure images are between the desired amount of 8 - 18
    while not (8 <= len(frames) <= 18):
        if len(frames) < 8:
            # Increase fps to the next higher option if below the minimum frame count
            current_index = FPS_OPTIONS.index(fps)
            if current_index < len(FPS_OPTIONS) - 1:
                fps = FPS_OPTIONS[current_index + 1]
            else:
                # If already at max fps and frames are still not enough, exit the loop
                break
        elif len(frames) > 18:
            # Decrease fps to the next lower option if above the maximum frame count
            current_index = FPS_OPTIONS.index(fps)
            if current_index > 0:
                fps = FPS_OPTIONS[current_index - 1]
            else:
                # If already at minimum fps and frames are still too many, exit the loop
                break

        frames = extract_frames_from_video(
            video_path,
            start_frame=expanded_start,
            end_frame=expanded_end,
            fps=fps,
        )


    if action_dict["action_type"] == "pick":
        timestep_prompt = LABEL_PICKUP_ACTION.format(
            action=action_dict["action"], object=action_dict["object"]
        )
    else:
        timestep_prompt = LABEL_DEPOSIT_ACTION.format(
            action=action_dict["action"], object=action_dict["object"]
        )

    response = await vlm_request(
        client, SYSTEM_PROMPT, timestep_prompt, frames, temperature=0, extract_json=True
    )

    if response is None:
            return None
    
    start_image_number = response.get("start_image")
    end_image_number = response.get("end_image")

    if start_image_number is None or end_image_number is None: 
        return None
    
    start_frame = expanded_start + (start_image_number - 1) * video_fps / fps
    if action_dict["action_type"] == "pick":
        start_frame -= 15 # adjusting half a second to capture more context
    end_frame = expanded_start + (end_image_number) * video_fps / fps

    result = {
        "action": action_dict["action"],
        "start_image": start_image_number,
        "end_image": end_image_number,
        "start_frame": start_frame,
        "end_frame": end_frame,
        "fps": fps,
        "action_type": action_dict["action_type"],
        "object": action_dict["object"],
    }

    return result


def define_pick_prompts(action, object_name):
    return {
        "start_label_prompt": REFINED_START_FRAME_PICK.format(action=action, object=object_name),
        "end_label_prompt": REFINED_END_FRAME_PICK.format(action=action, object=object_name),
        "start_check_prompt": CHECK_PICKUP_START_IMAGE_TIMING.format(action=action, object=object_name),
        "end_check_prompt": CHECK_PICKUP_END_IMAGE_TIMING.format(action=action, object=object_name)
    }

def define_put_prompts(action, object_name):
    return {
        "start_label_prompt": REFINED_START_FRAME_DEPOSIT.format(action=action, object=object_name),
        "end_label_prompt": REFINED_END_FRAME_DEPOSIT.format(action=action, object=object_name),
        "start_check_prompt": CHECK_DEPOSIT_START_IMAGE_TIMING.format(action=action, object=object_name),
        "end_check_prompt": CHECK_DEPOSIT_END_IMAGE_TIMING.format(action=action, object=object_name),
    }



# async def adjust_frames_for_action(action_dict, client, video_path, fps):
#     """Process a single robot task by calculating the range, getting frames, and analyzing the task."""
#     action_type = action_dict["action_type"]
#     action = action_dict["action"]
#     object_name = action_dict["object"]
#     start_check = action_dict["start_check"]
#     counter= 0

#     # only for pick start frame
#     while start_check == "wrong_object" and counter <= 3: 
        
#         action_dict["start_frame"] += 30

#         frames, _ = adjust_fps_to_frame_count(
#             video_path, action_dict["start_frame"], action_dict["end_frame"], fps, 5, 20
#         )

#         start_image_number = await vlm_request(
#             client, SYSTEM_PROMPT, REFINED_START_FRAME_PICK, frames, extract_json=True
#         )

#         action_dict["start_frame"] += (start_image_number['answer'] - 1) * 30 / fps

#         frames, _ = adjust_fps_to_frame_count(
#             video_path, action_dict["start_frame"], action_dict["end_frame"], fps, 5, 20
#         )

#         start_check = await vlm_request(
#                 client,
#                 SYSTEM_PROMPT,
#                 CHECK_PICKUP_START_IMAGE_TIMING,
#                 frames,
#                 temperature=0.2,
#                 extract_json=True,
#             )
        
#         counter += 1
#         print(f"the action is: {action_dict['action']} and the check is: {start_check} after round {counter}")
    
#     action_dict = adjust_task_frame(action_dict)

#     if not action_dict["need_modification"]:
#         return action_dict

#     counter = 0 # reset it
#     while action_dict["need_modification"] and counter <3:
#         print(f"action failing here is: {action_dict['action']}")

#         if action_type == "pick":
#             prompts = define_pick_prompts(action, object_name)
#         elif action_type == "put":
#             prompts = define_put_prompts(action, object_name)
#         else:
#             raise ValueError(f"Unsupported task type: {action_type}")

#         if action_dict["start_check"] != "perfect":
#             frames = extract_frames_from_video(
#                 video_path, start_frame=action_dict["modified_start_start_frame"], end_frame=action_dict["modified_start_end_frame"], fps=fps
#             )
#             start_frame = await vlm_request(
#                 client,
#                 SYSTEM_PROMPT,
#                 prompts["start_label_prompt"],
#                 frames,
#                 temperature=0.2,
#                 extract_json=True,
#             )

#             if start_frame is None: 
#                 continue
#             start_image_number = start_frame.get("answer")
#             if start_image_number is None: 
#                 continue
            
#             action_dict["modified_start_start_frame"] += (start_image_number - 1) * 30 / fps
#             frames = extract_frames_from_video(
#                 video_path, start_frame=action_dict["modified_start_start_frame"], end_frame=action_dict["modified_start_end_frame"], fps=fps
#             )

#             if len(frames)==0: 
#                 continue

            
#             check_response = await vlm_request(
#                 client,
#                 SYSTEM_PROMPT,
#                 prompts["start_check_prompt"],
#                 frames,
#                 temperature=0.2,
#                 extract_json=True,
#             )


#             action_dict["start_check"] = check_response["answer"]
#             if action_dict["start_check"] == "perfect": 
#                 print('\n\n')
#                 print(f"check_response for {action_dict['action']} is {check_response}")
#                 print(f"modified_start_frame for {action_dict['action']} is: {action_dict['modified_start_start_frame']} and modified_end_frame is {action_dict['modified_start_end_frame']}")
#                 print('\n\n')
#                 action_dict["start_frame"] = action_dict["modified_start_start_frame"]
#             else: 
#                 print('\n\n')
#                 print(f"check_response for {action_dict['action']} is {check_response}")
#                 print(f"modified_start_frame for {action_dict['action']} is: {action_dict['modified_start_start_frame']} and modified_end_frame is {action_dict['modified_start_end_frame']}")
#                 print('\n\n')

#         if action_dict["end_check"] != "perfect":

#             frames = extract_frames_from_video(
#                 video_path, start_frame=action_dict["modified_end_start_frame"], end_frame=action_dict["modified_end_end_frame"], fps=fps
#             )
#             end_frame = await vlm_request(
#                 client,
#                 SYSTEM_PROMPT,
#                 prompts["end_label_prompt"],
#                 frames,
#                 temperature=0.2,
#                 extract_json=True,
#             )

#             if end_frame is None: 
#                 continue
#             end_image_number = end_frame.get("answer")
#             if end_image_number is None: 
#                 continue

            

#             action_dict["modified_end_end_frame"] = action_dict["modified_end_start_frame"]+ end_image_number * 30 / fps
#             frames = extract_frames_from_video(
#                 video_path, start_frame=action_dict["modified_end_start_frame"], end_frame=action_dict["modified_end_end_frame"], fps=fps
#             )

#             if len(frames)==0: 
#                 continue

#             check_response = await vlm_request(
#                 client,
#                 SYSTEM_PROMPT,
#                 prompts["end_check_prompt"],
#                 frames,
#                 temperature=0.2,
#                 extract_json=True,
#             )

#             action_dict["end_check"] = check_response["answer"]
#             if action_dict["end_check"] == "perfect": 
#                 print('\n\n')
#                 print(f"check_response for {action_dict['action']} is {check_response}")
#                 print(f"modified_start_frame for {action_dict['action']} is: {action_dict['modified_end_start_frame']} and modified_end_frame is {action_dict['modified_end_end_frame']}")
#                 print('\n\n')
#                 action_dict["end_frame"] = action_dict["modified_end_end_frame"]
#             else: 
#                 print('\n\n')
#                 print(f"check_response for {action_dict['action']} is {check_response}")
#                 print(f"modified_start_frame for {action_dict['action']} is: {action_dict['modified_end_start_frame']} and modified_end_frame is {action_dict['modified_end_end_frame']}")
#                 print('\n\n')
        
#         # Re-evaluate need for modification
#         action_dict["need_modification"] = (
#             action_dict["start_check"] != "perfect" or action_dict["end_check"] != "perfect"
#         )

#         counter += 1

#         if counter >= 3:
#             action_dict["start_frame"] = action_dict["modified_start_start_frame"]
#             action_dict["end_frame"] = action_dict["modified_end_end_frame"]

#     return action_dict



async def adjust_frames_for_action(action_dict, client, video_path, fps):
    """Process a single robot task by calculating the range, getting frames, and analyzing the task."""
    action_type = action_dict["action_type"]
    action = action_dict["action"]
    object_name = action_dict["object"]
    start_check = action_dict["start_check"]
    counter= 0

    # only for pick start frame
    while start_check == "wrong_object" and counter <= 3: 
        # pdb.set_trace()
        start_frame = action_dict["start_frame"] + 30
        # action_dict["start_frame"] += 30

        frames, _ = adjust_fps_to_frame_count(
            video_path, start_frame, action_dict["end_frame"], fps, 5, 20
        )

        start_image_number = await vlm_request(
            client, SYSTEM_PROMPT, REFINED_START_FRAME_PICK, frames, extract_json=True
        )

        start_frame += (start_image_number['answer'] - 1) * 30 / fps

        frames, _ = adjust_fps_to_frame_count(
            video_path, start_frame, action_dict["end_frame"], fps, 5, 20
        )

        start_check_json = await vlm_request(
                client,
                SYSTEM_PROMPT,
                CHECK_PICKUP_START_IMAGE_TIMING,
                frames,
                temperature=0,
                extract_json=True,
            )
        
        if start_check_json is None: 
            action_dict["start_frame"] -= 30
            continue
        start_check = start_check_json.get("answer")
        if start_check is None: 
            action_dict["start_frame"] -= 30
            continue
        

        action_dict["start_check"] = start_check
        action_dict["start_frame"] = start_frame

        counter += 1
        print(f"the action is: {action_dict['action']} and the check is: {start_check} after round {counter} and start frame is {action_dict['start_frame']}")
    
    action_dict = adjust_task_frame(action_dict)

    if not action_dict["need_modification"]:
        return action_dict

    counter = 0 # reset it
    while action_dict["need_modification"] and counter <3:
        print(f"action failing here is {action_dict['action']}. Start check is {action_dict['start_check']} and end check is {action_dict['end_check']}")

        if action_type == "pick":
            prompts = define_pick_prompts(action, object_name)
        elif action_type == "put":
            prompts = define_put_prompts(action, object_name)
        else:
            raise ValueError(f"Unsupported task type: {action_type}")

        if action_dict["start_check"] != "perfect":
            frames = extract_frames_from_video(
                video_path, start_frame=action_dict["modified_start_start_frame"], end_frame=action_dict["modified_start_end_frame"], fps=fps
            )
            start_frame = await vlm_request(
                client,
                SYSTEM_PROMPT,
                prompts["start_label_prompt"],
                frames,
                temperature=0.2,
                extract_json=True,
            )

            if start_frame is None: 
                continue
            start_image_number = start_frame.get("answer")
            if start_image_number is None: 
                continue
            
            action_dict["modified_start_start_frame"] += (start_image_number - 1) * 30 / fps
            frames = extract_frames_from_video(
                video_path, start_frame=action_dict["modified_start_start_frame"], end_frame=action_dict["modified_start_end_frame"], fps=fps
            )

            if len(frames)==0: 
                continue

            
            check_response = await vlm_request(
                client,
                SYSTEM_PROMPT,
                prompts["start_check_prompt"],
                frames,
                temperature=0.2,
                extract_json=True,
            )


            action_dict["start_check"] = check_response["answer"]
            if action_dict["start_check"] == "perfect": 
                print('\n\n')
                print(f"start check_response for {action_dict['action']} is {action_dict['start_check']}")
                print(f"modified_start_frame for {action_dict['action']} is: {action_dict['modified_start_start_frame']} and modified_end_frame is {action_dict['modified_start_end_frame']}")
                print('\n\n')
                action_dict["start_frame"] = action_dict["modified_start_start_frame"]
            else: 
                print('\n\n')
                print(f"start check_response for {action_dict['action']} is {action_dict['start_check']}")
                print(f"modified_start_frame for {action_dict['action']} is: {action_dict['modified_start_start_frame']} and modified_end_frame is {action_dict['modified_start_end_frame']}")
                print('\n\n')

        if action_dict["end_check"] != "perfect":

            frames = extract_frames_from_video(
                video_path, start_frame=action_dict["modified_end_start_frame"], end_frame=action_dict["modified_end_end_frame"], fps=fps
            )
            end_frame = await vlm_request(
                client,
                SYSTEM_PROMPT,
                prompts["end_label_prompt"],
                frames,
                temperature=0.2,
                extract_json=True,
            )

            if end_frame is None: 
                continue
            end_image_number = end_frame.get("answer")
            if end_image_number is None: 
                continue

            

            action_dict["modified_end_end_frame"] = action_dict["modified_end_start_frame"]+ end_image_number * 30 / fps
            frames = extract_frames_from_video(
                video_path, start_frame=action_dict["modified_end_start_frame"], end_frame=action_dict["modified_end_end_frame"], fps=fps
            )

            if len(frames)==0: 
                continue

            check_response = await vlm_request(
                client,
                SYSTEM_PROMPT,
                prompts["end_check_prompt"],
                frames,
                temperature=0.2,
                extract_json=True,
            )

            action_dict["end_check"] = check_response["answer"]
            if action_dict["end_check"] == "perfect": 
                print('\n\n')
                print(f"end check_response for {action_dict['action']} is {action_dict['end_check']}")
                print(f"modified_start_frame for {action_dict['action']} is: {action_dict['modified_end_start_frame']} and modified_end_frame is {action_dict['modified_end_end_frame']}")
                print('\n\n')
                action_dict["end_frame"] = action_dict["modified_end_end_frame"]
            else: 
                print('\n\n')
                print(f"end check_response for {action_dict['action']} is {action_dict['end_check']}")
                print(f"modified_start_frame for {action_dict['action']} is: {action_dict['modified_end_start_frame']} and modified_end_frame is {action_dict['modified_end_end_frame']}")
                print('\n\n')


        
        # Re-evaluate need for modification
        action_dict["need_modification"] = (
            action_dict["start_check"] != "perfect" or action_dict["end_check"] != "perfect"
        )

        print(f"reneed to modify is: {action_dict['need_modification']}")

        counter += 1

        if counter >= 3:
            action_dict["start_frame"] = action_dict["modified_start_start_frame"]
            action_dict["end_frame"] = action_dict["modified_end_end_frame"]

    return action_dict



async def adjusting_frames_in_episode(client, video_path, labeled_results, fps=5):
    # adjusted_tasks = adjust_task_frames(labeled_results)
    # adjusted_tasks=labeled_results

    tasks_to_process = [adjust_frames_for_action(copy.deepcopy(action), client, video_path, fps) for action in labeled_results]
    responses = await asyncio.gather(*tasks_to_process)
    filtered_responses = [response for response in responses if response is not None]

    return filtered_responses



