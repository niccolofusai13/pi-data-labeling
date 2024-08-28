import asyncio
from video_labeling.utils import extract_frames_from_video, adjust_fps_to_frame_count
from video_labeling.prompts.find_objects import (
    FIND_OBJECTS_SYSTEM_PROMPT,
    FIND_OBJECTS,
)

from video_labeling.prompts.shared import SYSTEM_PROMPT
from video_labeling.utils import (
    vlm_request,
)


# async def identify_moved_objects(client, video_path, video_chunks, fps=3):
#     """Identifying which objects have moved positions in the chunks"""
#     tasks = []
#     for start, end in video_chunks:
#         frames = extract_frames_from_video(video_path, start, end, fps=fps)
#         tasks.append(
#             vlm_request(
#                 client,
#                 FIND_OBJECTS_SYSTEM_PROMPT,
#                 FIND_OBJECTS,
#                 frames,
#                 extract_json=True,
#             )
#         )

#     moved_objects = await asyncio.gather(*tasks)

#     return moved_objects

async def identify_moved_objects(client, video_path, video_chunks, fps=3):
    """Identifying which objects have moved positions in the chunks"""
    tasks = []
    for start, end in video_chunks:
        frames, fps = adjust_fps_to_frame_count(video_path, start, end, fps, 8, 22)

        # frames = extract_frames_from_video(video_path, start, end, fps)
        print(len(frames))
        tasks.append(
            vlm_request(
                client,
                SYSTEM_PROMPT,
                FIND_OBJECTS,
                frames,
                extract_json=True,
            )
        )

    moved_objects = await asyncio.gather(*tasks)

    return moved_objects
