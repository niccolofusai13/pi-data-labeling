FIND_OBJECTS_SYSTEM_PROMPT = """

You will be presented with images of a specific environment featuring a table with various objects and a robot arm performing actions. The environment includes the following components:

**Environment and Components:**
- **Potential Objects:**
  - Cup
  - Packets
  - Containers 
  - Lids
  - Food containers (plastic / aluminium / cardboard)
  - Chopstick
  - Bottle
  - Bowl
  - Plate
  - Spoon
- **Destinations:**
  - Box (big box on top of the table where items go into)
  - Trash Bin (next to the table)
- **Robot Mechanism:**
  - Robot Arm equipped with a Gripper

"""



FIND_OBJECTS = """
Identify objects that are lifted by the robot gripper above the table in a sequence of images.

**Instructions:**
- Review the series of images to determine which objects are lifted by the robot gripper and held in the air above the table.
- List only those objects that are clearly gripped and elevated above the table surface in at least three consecutive images. This ensures accuracy in identifying objects that the robot is intentionally manipulating.
- Pay special attention to objects that may be stacked on top of one another. Ensure accurate identification especially when the robot manipulates an object from a stack. It is crucial to confirm whether the topmost or another specific object is being lifted.

**Criteria for Inclusion:**
- The object must be in the air, held by the gripper, not merely touched or moved along the table surface.
- The object must be clearly above the table.
- The grip on the object must be visible and stable across at least three consecutive images.
- Special attention should be given to any objects that are part of a stack. Verify that the object identified as lifted is indeed the one being manipulated by the gripper.

**Format:**
Start with your reasoning based on the observations from the images, followed by the JSON formatted answer. Include concise descriptions for each object identified.
If no objects meet the criteria in the images provided, return an empty list in the JSON object.

**Example Answer:**
[Reasoning]
{
  "lifted_objects": [
    "Spoon",
    "Cup"
  ]
}
"""



# FIND_OBJECTS = """
# **Identify Every Actions Performed by the Robot in a Video Sequence**

# **Instructions:**
# - Review the series of images to track objects that are manipulated by the robot gripper.
# - Determine every single object that is picked up and where it is placed by the robot. Only report actions involving objects that are manipulated in accordance with the defined action criteria.
# - Pay special attention to objects that may be stacked on top of one another, ensuring accurate identification when the robot manipulates an object from a stack.

# **Criteria for Actions:**
# 1. **Pick Up Action**:
#    - The object must be visibly gripped by the gripper and lifted off the table surface.
#    - The grip must be stable and visible in at least three consecutive images.

# 2. **Put Action**:
#    - The object must be placed into a designated destination (Box or Trash Bin).
#    - Ensure the object is confirmed inside the destination and the gripper has retracted completely.

# **Object Destination Rules:**
# - Check carefully where the object being deposited ends up. Anything that could be trash (like packets) often go into the trash. 
# - Plates, bowls, spoons, cups or stuff that we want to keep often goes into the box. For containers, you should check carefully where it is being deposited.

# **Format for Reporting:**
# Provide a detailed reasoning based on your observations from the images, followed by a JSON formatted answer. Include concise descriptions of each object's actions.

# **Example Answer:**
# [Reasoning]
# ```json
# {{
#   "actions": [
#     "Pick up Bowl",
#     "Put Bowl into Box"
#   ]
# }}
# """


# FIND_OBJECTS = """
# **Objective:**
# Identify and report every pick up and put down action performed by the robot in a video sequence.

# **Instructions:**
# - Observe the sequence of images to track every action where the robot manipulates objects.
# - Note each action as either "pick up OBJECT" when the robot lifts an object from the table, or "put OBJECT into DESTINATION" when the robot places an object into either a container/box on the table or the trash bin.
# - Ensure each action is observable and clear in the imagery, requiring visibility in at least three consecutive images for verification.

# **Action Details:**
# - **Pick Up Action**:
#    - Ensure the object is clearly gripped by the gripper and lifted off the table surface.

# - **Put Action**:
#    - Verify that the object is placed into a specific destination (Box or Trash Bin) and the gripper has completely retracted.

# **Destination Rules:**
# - Items likely to be trash (like packets) should generally be placed into the trash bin.
# - Reusable items (such as plates, bowls, spoons, cups) are usually placed into the box.

# **Format for Reporting:**
# Summarize each action observed in the video. For clarity, describe the action involving the object and its destination. Use a JSON formatted response for structured reporting.

# **Example Summary Report:**
# [Reasoning]
# ```json
# {{
#   "actions": [
#     "Pick up Bowl",
#     "Put Bowl into Box"
#   ]
# }}
# """