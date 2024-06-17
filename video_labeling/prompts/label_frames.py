# Step 2
LABEL_PICKUP_ACTION = """
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
```json
{{
"start_image":2,
"end_image":8
}}
"""

LABEL_DEPOSIT_ACTION = """
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
```json
{{
"start_image":2,
"end_image":8
}}
"""


TEST_LABEL_PICKUP= """
### Analyze the Robot's Pickup Task: {action}

**Context:**
You are assigned to analyze a sequence in which a robot attempts to pickup {object}. The aim is to identify the correct START and END image that matches the criteria below.

**Helpful information:**: 
To check if an object is grasped, check if the robot grippers are holding anything. 
If an object is no longer visible on the table, and is not in the robot's gripper, it means it has been deposited in the destination.
If the task is to place the object in the bin, once deposited you are not able to see the object any more. 
The black chopstick is often hard to see, especially when grasped. Please pay special attention if the object is the black chopstick.

**Criteria needeed for successful START image for depositing an object:**
- In the first image, the {object} needs to be *starting* lifted above the table (to any degree).
- In the first image, the {object} needs to be not have been released yet.

**Criteria needeed for successful END image for depositing an object:**
- In the final image, the {object} is no longer airborn. 
- In the final image, the {object} was placed into one of the bin or plastic container

**Instruction:**
From the images above, which image best describes the START and END image criteria above.

After reasoning about the answer, return a JSON for your answer.
Example:  
```json
{{
  "start_image": 7,
  "end_image": 10
}}
"""

TEST_LABEL_PICKUP = """
### Analyze the Robot's Pickup Task: {action}

**Context:**
You are assigned to analyze a sequence in which a robot attempts to pick up {object}. The aim is to identify the correct START and END image that matches the criteria below.

**Helpful information:**: 
To check if an object is grasped, check if the robot grippers are holding anything. 
If an object is no longer visible on the table, and is not in the robot's gripper, it means it has been deposited in the destination.
The black chopstick is often hard to see, especially when grasped. Please pay special attention if the object is the black chopstick.

**Criteria needeed for successful START image for PICK UP:**
- In the first image, the {object} needs to be on the table 
- In the first image, there is some space between the gripper and the {object}
- In the first image, the robot has not yet grasped the object

**Criteria needeed for successful END image for picking up:**
- In the final image, the {object} has been lifted off the table, enough to see space between the object and the table.
- In the final image, the {object} is grasped by the robot

**Instruction:**
From the images above, which images best describe the START and END image based on the criteria above.

After reasoning about the answer, return a JSON for your answer.
Example:  
```json
{{
  "start_image": 2,
  "end_image": 8
}}
"""

TEST_LABEL_DEPOSIT= """
### Analyze the Robot's Putting Task: {action}

**Context:**
You are assigned to analyze a sequence in which a robot attempts to deposit an {object} into a destination. The aim is to identify the correct START and END image that matches the criteria below.

**Helpful information:**: 
To check if an object is grasped, check if the robot grippers are holding anything. 
If an object is no longer visible on the table, and is not in the robot's gripper, it means it has been deposited in the destination.
If the task is to place the object in the bin, once deposited you are not able to see the object any more. 
The black chopstick is often hard to see, especially when grasped. Please pay special attention if the object is the black chopstick.

**Criteria needeed for successful START image for depositing an object:**
- In the first image, the {object} needs to be *starting* lifted above the table (to any degree).
- In the first image, the {object} needs to be not have been released yet.

**Criteria needeed for successful END image for depositing an object:**
- In the final image, the {object} is no longer airborn. 
- In the final image, the {object} was placed into one of the bin or plastic container

**Instruction:**
From the images above, which images best describe the START and END image based on the criteria above.

After reasoning about the answer, return a JSON for your answer.
Example:  
```json
{{
  "start_image": 7,
  "end_image": 10
}}
"""

# Step 3
LABEL_PICKUP_ACTION_HIGHER_FPS = """
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

**Sample Response:**
[Explanation]
```json
{{
  "start_image": 2,
  "end_image": 8
}}
"""

LABEL_DEPOSIT_ACTION_HIGHER_FPS = """
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

**Sample Response:**
[Explanation]
```json
{{
  "start_image": 2,
  "end_image": 9
}}
"""

# Relabel frames but start and end frame seperately with even higher FPS
REFINED_START_FRAME_PICK = """
### Analyze the Robot's Pickup Task: {action}

**Context:**
You are assigned to analyze a sequence in which a robot attempts to pick up {object}. The aim is to identify the correct START image that matches the criteria below.

**Helpful information:**: 
To check if an object is grasped, check if the robot grippers are holding anything. 
If an object is no longer visible on the table, and is not in the robot's gripper, it means it has been deposited in the destination.
The black chopstick is often hard to see, especially when grasped. Please pay special attention if the object is the black chopstick.

**Criteria needeed for successful START image for PICK UP:**
- In the first image, the {object} needs to be on the table 
- In the first image, there is some space between the gripper and the {object}
- In the first image, the robot has not yet grasped the object

**Criteria needeed for successful END image for picking up:**
- In the final image, the {object} has been lifted off the table, enough to see space between the object and the table.
- In the final image, the {object} is grasped by the robot

**Instruction:**
From the images above, which image best describes the START image criteria above.

After reasoning about the answer, return a JSON for your answer.
Example:  
```json
{{
"answer":3
}}
"""


REFINED_END_FRAME_PICK = """
### Analyze the Robot's Pickup Task: {action}

**Context:**
You are assigned to analyze a sequence in which a robot attempts to pick up {object}. The aim is to identify the correct END image that matches the criteria below.

**Helpful information:**: 
To check if an object is grasped, check if the robot grippers are holding anything. 
If an object is no longer visible on the table, and is not in the robot's gripper, it means it has been deposited in the destination.
The black chopstick is often hard to see, especially when grasped. Please pay special attention if the object is the black chopstick.

**Criteria needeed for successful START image for PICK UP:**
- In the first image, the {object} needs to be on the table 
- In the first image, there is some space between the gripper and the {object}
- In the first image, the robot has not yet grasped the object

**Criteria needeed for successful END image for picking up:**
- In the final image, the {object} has been lifted off the table, enough to see space between the object and the table.
- In the final image, the {object} is grasped by the robot

**Instruction:**
From the images above, which image best describes the END image criteria above.

After reasoning about the answer, return a JSON for your answer.
Example:  
```json
{{
"answer": 9
}}
"""


REFINED_START_FRAME_DEPOSIT = """
### Analyze the Robot's Putting Task: {action}

**Context:**
You are assigned to analyze a sequence in which a robot attempts to deposit an {object} into a destination. The aim is to identify the correct START image that matches the criteria below.

**Helpful information:**: 
To check if an object is grasped, check if the robot grippers are holding anything. 
If an object is no longer visible on the table, and is not in the robot's gripper, it means it has been deposited in the destination.
If the task is to place the object in the bin, once deposited you are not able to see the object any more. 
The black chopstick is often hard to see, especially when grasped. Please pay special attention if the object is the black chopstick.

**Criteria needeed for successful START image for depositing an object:**
- In the first image, the {object} needs to be *starting* lifted above the table (to any degree).
- In the first image, the {object} needs to be not have been released yet.

**Criteria needeed for successful END image for depositing an object:**
- In the final image, the {object} is no longer airborn. 
- In the final image, the {object} was placed into one of the bin or plastic container

**Instruction:**
From the images above, which image best describes the START image criteria above.

After reasoning about the answer, return a JSON for your answer.
Example:  
```json
{{
"answer":3
}}
"""


REFINED_END_FRAME_DEPOSIT = """
### Analyze the Robot's Putting Task: {action}

**Context:**
You are assigned to analyze a sequence in which a robot attempts to deposit an {object} into a destination. The aim is to identify the correct START image that matches the criteria below.

**Helpful information:**: 
To check if an object is grasped, check if the robot grippers are holding anything. 
If an object is no longer visible on the table, and is not in the robot's gripper, it means it has been deposited in the destination.
If the task is to place the object in the bin, once deposited you are not able to see the object any more. 
The black chopstick is often hard to see, especially when grasped. Please pay special attention if the object is the black chopstick.

**Criteria needeed for successful START image for depositing an object:**
- In the first image, the {object} needs to be *starting* lifted above the table (to any degree).
- In the first image, the {object} needs to be not have been released yet.

**Criteria needeed for successful END image for depositing an object:**
- In the final image, the {object} is no longer airborn. 
- In the final image, the {object} was placed into one of the bin or plastic container

**Instruction:**
From the images above, which image best describes the END image criteria above.

After reasoning about the answer, return a JSON for your answer.
Example:  
```json
{{
"answer": 9
}}

"""
