DIFFERENCE_IN_IMAGES_SYSTEM_PROMPT = """

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


DIFFERENCE_IN_IMAGES_QUESTION = """
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

SYSTEM_PROMPT = """
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

**Helpful Information:**
The object detection model has detected that the following objects have moved: 
{moved_objects}

**Example Summary Report:**
{{
  "tasks": [
    {{
      "task": "Pick up Plastic Bowl",
      "details": "Plastic bowl clearly in the robot gripper, has been picked up from the table and is clearly suspended in the air.",
      "image_range": "2-8",
      "object": "Plastic Bowl"
    }},
    {{
      "task": "Put Plastic Bowl into Clear Plastic Box",
      "details": "After picking up, the plastic bowl is observed being placed into the plastic box. The task is confirmed complete as the robot's gripper retracts and the plastic bowl is no longer in contact with the gripper.",
      "image_range": "7-9",
      "object": "Plastic Bowl"
    }}
  ]
}}

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
- The robot's gripper should be closed, holding the relevant object in the air.
- It should be AFTER picking up the object, but BEFORE moving it to the destination. 

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

It is criitical you stick closely to the criteria above. 
"""


PICK_UP_TIMESTEP_PROMPT_TEMPLATE = """
### **Robot Task Analysis: “Pick Up” Mission**

**Introduction:**
Welcome to the task analysis module. You are about to engage in a mission to review a sequence of {num_images} chronological images displaying a robot’s attempt to perform a specific action: "{action}". Your objective is to accurately identify the pivotal moments where the action initiates and concludes.

**Detailed Mission Guidelines:**

#### **Identification of Start Image:**
- **Visual Cue:** Search for the frame where the robot’s gripper appears open and devoid of any contents.
- **Positional Cue:** Ensure there is a visible space between the gripper and the target object, indicating no contact.
- **Action Cue:** The start image should capture the moment the robot initiates movement towards the object, indicating the beginning of the pick-up process, but importantly has not made contact yet. 

#### **Identification of End Image:**
- **Visual Cue:** Locate the frame where the gripper is fully closed, securely holding the object.
- **Positional Cue:** Confirm that the object is elevated (picked up) and clearly separated from its original resting place on the table.
- **Action Cue:** The end image should clearly depict the object in mid-air, held by the robot, just after the robot has lifted it, indicating a successful pick-up.

**Example Submission:**

{{
  "start_image": 3,
  "end_image": 12
}}

"""


PUT_OBJECT_TIMESTEP_PROMPT_TEMPLATE = """
### **Robot Task Analysis: “Place Object” Mission**

**Introduction:**
You are tasked with reviewing a sequence of {num_images} images that document the robot performing "{action}". Your challenge is to determine the key frames that signify the beginning and the end of this placement action.

#### **Identification of Start Image:**
- **Visual Cue:** Identify the frame showing the robot’s gripper closed around the object, clearly in the air.This happens after being picked up but before being dropped. 
- **Positional Cue:** The selected frame should be captured before the robot commences its motion towards the destination, holding the object in the gripper.
- **Action Cue:** This frame marks the readiness to move toward placing the object, avoiding any frames where the gripper is already over the destination.

#### **Identification of End Image:**
- **Visual Cue:** Find the frame where the gripper has just released the object into its designated place (either the bin or the container).
- **Positional Cue:** Ensure that there is notable space between the gripper and the object, indicating that the object is now resting within its destination.
- **Action Helper:** The frame should capture the moment JUST after the object is released and the object is clearly in the destination. 

**Example Submission:**
{{
  "start_image": 5,
  "end_image": 9
}}

"""

PICKUP_REFINE_PROMPT_TEMPLATE = """
This is a video of a robot doing task: {action}. 
The first image in the video is the beginning of the action, and the final image is the end of the action. 

For tasks like pickup (which this is), there are very strict criteria which define what the beginning and end image should look like for this action. 

**Beginning image criteria**
- The robot gripper should not be in contact with any object
- The robot gripper should be about to begin its approach to {object}

**End image criteria**
- The {object} should be in the robot gripper, and airborn
- The {object} should not be dropped into any destination (the container / bin). The object should be in the closed gripper, ideally outside of the drop zone. 

In which image does the robot begin picking up the {object}, and in which image does the robot succesfully pick it up (before depositing it) 
Also make sure that if the robot is handling multiple objects in the series of images, you only pick out the ones associated with the object {object}

Example json output 1: 
[Explanation for answer]
{{
"start_image":2,
"end_image":8
}}

"""

DEPOSIT_REFINE_PROMPT_TEMPLATE = """
This is a video of a robot doing task: {action}. 
The first image in the video is the beginning of the action, and the final image is the end of the action. 

For tasks like putting into a destination (which this is), there are very strict criteria which define what the beginning and end image should look like for this action. 

**Beginning image criteria**
- The {object} should be in the robot gripper, and the object should be in the air, above the table. 
- The {object} should not be released from the robot gripper, and should not be vertically over the destination (the container or the bin)

**End image criteria**
- The {object} should be deposited in the final destination (the container or the bin)
- The robot gripper should have retreated slightly

In which image does the robot begin depositing the {object}, and in which image does the robot succesfully finish depositing it. 
Also make sure that if the robot is handling multiple objects in the series of images, you only pick out the ones associated with the object {object}

Example json output 1: 
[Explanation for answer]
{{
"start_image":2,
"end_image":8
}}


"""

DEPOSIT_ZOOM_IN_PROMPT_TEMPLATE = """
### Analyze the Robot's Depositing Task: {action}

**Context:**
You are tasked with analyzing a sequence where a robot is engaged in depositing {object} into its designated destination. Your role is to carefully examine the footage and determine the precise frames that mark the beginning and conclusion of the depositing action.

**Investigative Focus Points:**

**Start Image for Deposit:**
- **Observation 1:** Look for the frame where the robot’s gripper is securely holding {object}, which should be elevated and not yet over its final destination. If the {object} is already over the destination, the frame is too early, and the start image should be 'after' this one.
- **Observation 2:** The gripper should have just completed the pickup phase and be moving towards the destination (bin or container). If the gripper is stationary or moving away from the destination, the frame is too late, and the start image should be 'before' this one.

**End Image for Deposit:**
- **Observation 1:** Identify the frame where the gripper has released {object} into its designated spot. Ensure that the object is visibly settled within the destination. If the {object} is not yet released, the frame is too early, and the end image should be 'after' this one.
- **Observation 2:** Verify that there is a preceding image where {object} is seen already in the destination, ensuring continuity. If no such image exists, the action might not be fully captured, indicating the end image should be 'after'.
- **Observation 3:** Look for a clear retreat of the gripper from the destination, highlighting the separation between {object} and the gripper. If the gripper is still in contact with the {object}, the frame is too early, and the end image should be 'after' this one.

**Assignment:**
- Document the frame number that marks the initiation of the deposit action and the frame that signifies the completion of the placement.
- Maintain focus on {object} and disregard any interactions with other objects, unless they directly impact the depositing action.

**Response Structure:**
- Provide frame numbers for the start and end of the deposit action. 
- If the complete action is not captured within the provided frames, specify whether the necessary frames occur 'before' or 'after' the footage provided.

**Sample Response:**
[Explanation]
{{
  "start_image": 2,
  "end_image": 9
}}

"""

PICKUP_ZOOM_IN_PROMPT_TEMPLATE = """
### Analyze the Robot's Pickup Task: {action}

**Context:**
You are assigned to analyze a sequence in which a robot attempts to pick up {object}. The aim is to meticulously identify the exact frames that mark the start and conclusion of the pickup action.

**Investigative Focus Points:**

**Start Image for Pickup:**
- **Observation 1:** Seek the frame where the robot's gripper is not in contact with the object {object}. If the gripper is in contact, the image is too late, and the correct start image should be 'before' this one. Ensure the gripper is in a neutral, open position, prepared for the action.
- **Observation 2:** Confirm that the gripper does not hold any object. If the gripper holds an object, the image is too late, and the start image should be 'before'.

**End Image for Pickup:**
- **Observation 1:** Look for the frame where {object} is securely held and elevated above the table by the gripper. If the object is not yet picked up or still in contact with the table, the frame is too early, and the end image should be 'after' this one.
- **Observation 2:** Ensure that the {object} has not been deposited into any destination, such as a container or bin. If the object is already deposited, the image is too late, and the end image should be 'before' this one. The object should be in the air, clearly in the grippers.

**Assignment:**
- Determine and document the frame number that marks the initiation of the robot's pickup action and the frame that signifies the successful completion of the pickup.
- Pay meticulous attention to any multiple objects present in the sequence. Focus exclusively on frames involving {object} and ignore any frames where the robot interacts with other objects.

**Response Structure:**
- Provide frame numbers for the start and end of the pickup action. 
- If the action is not completely captured within the provided frames, specify whether the necessary frames occur 'before' or 'after' the footage provided.

**Sample Response:**
[Explanation]
{{
  "start_image": 2,
  "end_image": 8
}}

"""


VIDEO_DESCRIPTION = """
Please explain succintly what is happening in this video. 
"""


WRONG_OBJECT_CHECK = """
### Analyze the Robot's Action: {action}

**Context:**
Your goal is to verify this action in the images is the same action as {action}.

**Description of the video:**
{description}

**Instruction:**
Please answer the following question? 
- Are more than half of the images showing a task other than {action}? 

Reply with a simple yes or no and nothing else.
"""
