# pi-data-labeling

## Automating Data Labeling

The aim of this project is to create an automated data labeling platform.

## Installation

To set up the project environment, you can use `conda` to install the required dependencies. First, ensure you have `conda` installed, then run the following commands:

```sh
conda create --name pi python=3.10
conda activate pi
pip install -r requirements.txt
```

## Directory Structure

Here's a high-level overview of the directory structure for this project:

```
pi-data-labeling/
├── data/
│   ├── input/             # Input directory for mp4 video files
│   └── output/            # Output directory for labeled results
├── notebooks/             # Jupyter notebooks for exploratory analysis (needs cleaning #TODO)
├── qa/                    # Quality assurance scripts and metrics to test the system
├── streamlit_demo/        # Streamlit application for demonstrating the system
├── tests/                 # Unit tests for the project (currently empty)
└── video_labeling/        # Core code for video labeling
```

### Directory Details

- **data/input/**: This directory contains the input video files in mp4 format. These are the raw videos that need to be labeled.
- **data/output/**: This directory will store the results of the labeling process, including any annotated data and outputs.
- **notebooks/**: Jupyter notebooks used for exploratory data analysis
- **qa/**: Scripts and metrics used for quality assurance. These scripts help in testing and validating the system to ensure the accuracy and reliability of the labeled data.
- **streamlit_demo/**: A Streamlit application that provides a user-friendly interface to demonstrate the capabilities of the video labeling system.
- **tests/**: This directory is intended for unit tests to validate the functionality of the code. Currently, it is empty but will be populated with test scripts as development progresses.
- **video_labeling/**: Contains the core code and scripts responsible for the video labeling process. This is where the main logic lives.

## Getting Started

1. **Clone the repository**:
   ```sh
   git clone https://github.com/yourusername/pi-data-labeling.git
   cd pi-data-labeling
   ```

2. **Install dependencies**:
   Follow the installation instructions provided above to set up your environment using `conda` and install the required dependencies.

3. **Copy the environment configuration**:
   Copy the `.env.example` file to `.env` and update any necessary environment variables.
   ```sh
   cp .env.example .env
   ```

4. **Add your mp4 file**:
   Place your mp4 video file in the `data/input/` directory.

5. **Run the video labeling script**:
   ```sh
   python video_labeling/main.py
   ```

6. **Run the Streamlit demo**:
   Navigate to the `streamlit_demo` directory and start the Streamlit application to see the video labeling system in action.
   ```sh
   cd streamlit_demo
   streamlit run app.py
   ```

