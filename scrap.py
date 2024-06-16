
async def zoom_episode_timesteps(video_path, action, video_fps):
    """Process a single robot task by calculating the range, getting frames, and analyzing the task."""
    task_name = action["task_name"]
    task_type = action["task_type"]
    segment_start, segment_end = action['start_frame_of_segment'], action['end_frame_of_segment']
    sequence_fps = 5

        # Initial setup
    sequence_fps = 5
    fps_options = [3, 5, 10]  # Allowed fps values

    while True:
        print(f"task_name {task_name}, fps: {sequence_fps}")
        # Extract frames with the current fps setting
        frames = extract_frames_from_video(video_path, start_frame=segment_start, end_frame=segment_end, fps=sequence_fps)
        num_images = len(frames)
        print(f"task_name {task_name}, num_images: {num_images}")

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
    if task_type == 'pick':
        timestep_prompt = PICKUP_ZOOM_IN_PROMPT_TEMPLATE.format(
            action=task_name, object=action['object']
        )
    else:
        timestep_prompt = DEPOSIT_ZOOM_IN_PROMPT_TEMPLATE.format(
            action=task_name, object=action['object']
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
        "task_type": task_type
    }

    return result


async def zoom_video_timesteps(video_path, labeled_timesteps):
    tasks_to_process = []
    for action in labeled_timesteps:
        tasks_to_process.append(
            zoom_episode_timesteps(video_path, action, 30)
        )
    # Asynchronously process all tasks
    responses = await asyncio.gather(*tasks_to_process)
    return responses

