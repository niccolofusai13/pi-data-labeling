LABEL_ACTIONS = """
**Objective:**
Determine and report the actions successfully completed by a robot in a video sequence involving the manipulation of various objects.

**Summary Criteria:**
- Identify and list actions that have been conclusively completed. The object must be visibly manipulated by the robot’s gripper, and actions must include a clear transition from an initial to a final position.
- Ensure each reported action matches the visual evidence available in the video.
- Think carefully what the destination is, and follow the object destination rules above.

**High-Level Summary Instructions:**
Provide a summary of each action (Pick up and Put) that has been completed throughout the video. Specify the object involved and its final destination if applicable. Use the following example to guide your report:

**Helpful Information:**
The object detection model has detected that the following objects have moved: 
{moved_objects}

**Example Summary Report in JSON Format:**
{{
  "tasks": [
    {{
      "action": "Pick up Plastic Bowl",
      "details": "Plastic bowl clearly in the robot gripper, has been picked up from the table and is clearly suspended in the air.",
      "start_image": 2,
      "end_image": 7,
      "object": "Plastic Bowl"
    }},
    {{
      "action": "Put Plastic Bowl into Clear Plastic Box",
      "details": "After picking up, the plastic bowl is observed being placed into the plastic box. The action is confirmed complete as the robot's gripper retracts and the plastic bowl is no longer in contact with the gripper.",
      "start_image": 7,
      "end_image": 10,
      "object": "Plastic Bowl"
    }}
  ]
}}

**Instructions for Use:**
Use this format to create a coherent report on the actions observed in the video. Be specific about each action and ensure that the completion status is backed by clear visual evidence from the video. Do not make up any actions that are not shown in the images of the video. Please follow the Object Destination Rules
List the actions in chronological order.
"""
