import json
import asyncio
from openai import AsyncOpenAI
import os

from config import RESULTS_OUTPUT_PATH, OPENAI_API_KEY

from detect_objects import identify_moved_objects
from label_actions import label_actions_in_episode
from label_frames import (
    label_episode_frame_ranges,
    relabel_episode_frames_with_higher_fps,
    adjusting_frames_in_episode,
)
from checks import remove_erroneous_actions, run_checks

client = AsyncOpenAI(api_key=OPENAI_API_KEY)


async def label_video():

    print(f"Step 1: Identifying which objects have moved...")
    moved_objects = await identify_moved_objects()

    print(f"Step 2: Identifying which actions have taken place...")
    labeled_actions = await label_actions_in_episode(moved_objects)

    print(f"Step 3: Labeling the frame range...")
    labeled_frames = await label_episode_frame_ranges(labeled_actions)
    higher_fps_labeled_frames = await relabel_episode_frames_with_higher_fps(
        labeled_frames
    )

    print(f"Step 4: Removing erroneos actions...")
    qa_labels = await remove_erroneous_actions(higher_fps_labeled_frames, fps=5)

    print(f"Step 5: Running checks...")
    checks_feedback = await run_checks(qa_labels, fps=5)

    print(f"Step 6: Iteratively refining labels until all checks pass...")
    final_results = await adjusting_frames_in_episode(checks_feedback)

    print(f"Step 7: Done... saving results...")
    output_file_path = os.path.join(RESULTS_OUTPUT_PATH, "test_results.json")
    with open(output_file_path, "w") as file:
        json.dump(final_results, file, indent=4)


if __name__ == "__main__":
    asyncio.run(label_video())
