DIFFERENCE_IN_IMAGES_SYSTEM_PROMPT="""

You will be presented with images of a specific environment featuring a table with various objects and a robot arm performing tasks. The environment includes the following components:

**Environment and Components:**
- **Objects:**
  - Black Chopstick
  - Aluminum Container
  - Plastic Bowl
  - Metal Spoon
  - Cardboard Food Container
  - Glass Bowl
- **Destinations:**
  - Transparent Plastic Box (located on the black table)
  - Blue Bin (located next to the black table)
- **Robot Mechanism:**
  - Robot Arm equipped with a Gripper

**Task:**
Your task is to identify and list any changes in the video, specifically focusing on the objects.
"""


DIFFERENCE_IN_IMAGES_QUESTION="""
What has changed in the two images? Focus on the objects.

**Instructions:**
- Examine the images to determine which objects have moved or changed in any way.
- Return your answer as a JSON object listing only the objects that have moved or changed.

**Format:**
Return your answer as a JSON object, listing only the objects that have moved or changed.

**Example:**
{
  "moved_objects": [
    "Black Chopstick",
    "Plastic Bowl"
  ]
}

Only mention objects where you are 100% sure they have moved significantly. This means there must be a notable move in position between at least 2 images. Eg if the image is no longer in its starting position it has moved. 
Ignore the robot arm, focus only on the objects. Err on the side of caution when not sure. 
Think step by step.

"""

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

QUESTION = """
**Objective:**
Determine and report the tasks successfully completed by a robot in a video sequence involving the manipulation of various objects.

**Summary Criteria:**
- Identify and list tasks that have been conclusively completed. The object must be visibly manipulated by the robot’s gripper, and tasks must include a clear transition from an initial to a final position.
- Ensure each reported task matches the visual evidence available in the video.
- Think carefully what the destination is, and follow the object destination rules above.

**High-Level Summary Instructions:**
Provide a summary of each task type (Pick up and Put) that has been completed throughout the video. Specify the object involved and its final destination if applicable. Use the following example to guide your report:

**Example Summary Report:**
{
  "tasks": [
    {
      "task": "Pick up Plastic Bowl",
      "details": "Plastic bowl clearly in the robot gripper, has been picked up from the table and is clearly suspended in the air.",
      "image_range": "2-6"
    },
    {
      "task": "Put Plastic Bowl into Clear Plastic Box",
      "details": "After picking up, the plastic bowl is observed being placed into the plastic box. The task is confirmed complete as the robot's gripper retracts and the plastic bowl is no longer in contact with the gripper.",
      "image_range": "7-9"
    }
  ]
}

**Instructions for Use:**
Use this format to create a coherent report on the tasks observed in the video. Be specific about each task and ensure that the completion status is backed by clear visual evidence from the video. Do not make up any tasks that are not shown in the images of the video. It is important to remember the task definitions and what classifies as complete. Full compliance with the completion conditions is required to confirm each task.
List the tasks in chronological order.
"""

TIMESTEP_PROMPT_TEMPLATE = """
You are reviewing a specific action performed by a robot: {action}.
This review includes a sequence of {num_images} images that chronologically depict the robot executing the task within its operational environment.

**Objective:**
Determine and identify the start and end images that accurately frame the completion of the specified action.

**Criteria for Task Completion:**

### For "Pick Up" Tasks
Define the start and end images based on the following conditions:

***Start Image Criteria:***
- The robot's gripper should be open and empty.
- There should be no contact between the gripper and any object.
- A clear and noticeable space should exist between the target object and the robot's gripper.
- The 'start image' is the first image the robot starts to move towards the object, indicating the intent to pick it up.

***End Image Criteria:***
- The gripper is closed and has the relevant object in the gripper
- The object is in the air 
- There is significant space from the starting position of the object on the table and its current position
- The 'end image' should be as soon as the robot gripper has successfully picked up the object, and there is space between the table and the object in the gripper.

### For "Put Object Into" Tasks
Define the start and end images based on the following conditions:

***Start Image Criteria:***
- The robot's gripper should be closed, holding the relevant object.
- The robot gripper has just finished picking up the object and is about to start moving it towards the destination. 
- The 'start image' should be before the gripper has started to move to the Destination
- The 'start image' should NOT be when the gripper is hovering over the bin / container

***End Image Criteria:***
- The robot's gripper should be open, and not touching any object
- There must be signficant space between the destination of the object, and the current state of the robot gripper. 
- The gripper must have JUST retreated from the destination
- The 'end image' should NOT be when the gripper is hovering over the bin / container



**Response Format:**
Your response should specify the frame numbers for the start and end images that encapsulate the action.The response should be only a JSON, and nothing else.

**Example Output:**
{{
  "start_image": 3,
  "end_image": 12
}}
"""
