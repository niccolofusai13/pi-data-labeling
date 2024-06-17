FIND_OBJECTS_SYSTEM_PROMPT = """

You will be presented with images of a specific environment featuring a table with various objects and a robot arm performing actions. The environment includes the following components:

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


FIND_OBJECTS = """
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
