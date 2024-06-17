from dotenv import load_dotenv
import os

load_dotenv()

MODEL = os.getenv("MODEL", "gpt-4o")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
VIDEO_PATH = os.getenv("VIDEO_PATH", "data/pi_video_test.mp4")

# the size of the inital frame ranges for the first step of the process
FRAMES_SEGMENT_SIZE = int(os.getenv("FRAMES_SEGMENT_SIZE", "300"))

# only fps options are 3,5 or 10
FPS_OPTIONS = list(map(int, os.getenv("FPS_OPTIONS", "3,5,10").split(",")))

# directory to save the results
RESULTS_OUTPUT_PATH = os.getenv("RESULTS_OUTPUT_PATH", "data/output")

STREAMLIT_RESULTS_PATH = os.getenv(
    "STREAMLIT_RESULTS_PATH", "data/output/best_results.json"
)
