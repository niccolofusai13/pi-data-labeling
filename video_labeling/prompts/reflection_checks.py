
CHECK_PICKUP_START_IMAGE_TIMING = """
### Analyze the Robot's Pickup Action: {action}

**Context:**
You are tasked to analyze a sequence where a robot attempts to pick up {object}. The primary goal is to verify if the first image completely encapsulates the criteria for a successful start of the pickup action.

**Helpful Information:**
- If an object is no longer visible on the table and is not in the robot's gripper, it implies it has been deposited at the destination.
- The chopstick, if applicable, is often hard to see when grasped. Pay special attention if the object is a chopstick.

**Initial Check:**
- **Check 1:** Determine if the first object the robot holds in its gripper is {object}. If the robot is seen holding an object other than {object} in three consecutive images, respond with "wrong_object". 
The reason for having 3 consecutive images is that it prevents false positives like knocking over another object. To be the wrong_object, a different object than {object} needs to be in the roobot gripper for 3 seperate images. This check precedes any other analysis.

**Detailed Criteria for Pickup:**

**1. Start Image Criteria for Pickup:**
   - **Criterion 1:** The robot's gripper should not be holding any objects, including {object}.
   - **Criterion 2:** The robot's gripper should be positioned to soon pick up {object}, with visible space between the gripper and the object.
   - **Criterion 3:** The gripper should be positioned away from any objects, with subsequent frames showing the gripper moving towards {object} before picking it up.

**2. End Image Criteria for Pickup:**
   - **Criterion 1:** Identify the frame where {object} is securely held by the gripper and fully lifted off the table. If {object} is still touching the table, choose a later frame.
   - **Criterion 2:** Ensure that {object} has not started moving towards any destination like a bin or container. It should be just picked up, not yet moving towards the destination.
   - **Criterion 3:** The {object} should be firmly in the grasp of the robot. It should be above the table, and not close yet to the bin/container. If so, the image is too late.

**Instruction:**
- First, evaluate if the robot initially holds {object} in its gripper. If the first object held is not {object} and this is shown in three consecutive images, return "wrong_object". It is important for it to be shown in three consecutive images to avoid false positives.
- Next, evaluate if the first image strictly satisfies the criteria for the START image of this action {action}. Focus solely on the first image.

**Expected Response:**
- If the first object held in the gripper is not {object}, return "wrong_object".
- Otherwise, after reasoning about the answer based on the start image criteria, return a JSON indicating whether the START image for this action is "perfect", "early", or "late".

**Example Response:**
[Reasoning]
```json
{{
  "answer": "perfect"  // Options are "perfect", "early", "late", or "wrong_object"
}}
"""

CHECK_PICKUP_END_IMAGE_TIMING = """
### Analyze the Robot's Pickup Action: {action}

**Context:**
You are assigned to analyze a sequence in which a robot attempts to pick up {object}. The aim is to verify this if the final image FULLY encapsulates the criteria.

**Helpful information:**: 
To check if an object is grasped, check if the robot grippers are holding anything. 
If an object is no longer visible on the table, and is not in the robot's gripper, it means it has been deposited in the destination.
The chopstick is often hard to see, especially when grasped. Please pay special attention if the object is the chopstick.

**1. Start Image Criteria for Pickup:**
   - **Criterion 1:** The robot gripper should not be grasping or holding any objects, including `{object}`
   - **Criterion 2:** The robot gripper should be about to pick up `{object}`, but has some space in between the gripper and the object.
   - **Criterion 3:** The gripper should be positioned away from any objects, and the following frames should capture the robot gripper moving towards the `{object}`, before it picks it up. 

**2. End Image Criteria for Pickup:**
   - **Criterion 1:** Identify the image where `{object}` is securely held by the gripper and fully lifted off the table. If `{object}` is still touching the table, select a subsequent frame.
   - **Criterion 2:** Ensure that `{object}` has not yet started moving towards the destination (bin / container). It should have just been picked up, and not yet started its trajectory towards the destination.
   - **Criterion 3:** The {object} should be firmly in the grasp of the robot. It should be above the table, and not close yet to the bin / container. If so, the image is too late.

**Instruction:**
Evaluate if the last image strictly satisfies the criteria for the END image of this action {action}
Focus on evaluating the last image only.

After reasoning about the answer, return a JSON indicating whether the perfect END image for this action is "perfect" (meaning its the final image showed above), "early" (meaning the final image showed above is too early), or "late" (meaning the final image showed above is too late).

Example:  
[Reasoning]
```json 
{{
"answer":"perfect"    
}}
"""


CHECK_DEPOSIT_START_IMAGE_TIMING = """
### Analyze the Robot's Putting Action: {action}

**Context:**
You are assigned to analyze a sequence in which a robot attempts to deposit an {object} into a destination. The aim is to verify this if the first image FULLY encapsulates the criteria.

**Helpful information:**: 
To check if an object is grasped, check if the robot grippers are closed and holding the object. 
If an object is no longer visible on the table, and is not in the robot's gripper, it means it has been deposited in the destination.
The chopstick is often hard to see, especially when grasped. Please pay special attention if the object is the chopstick.

**1. Start Image Criteria for Deposit:**
   - **Criterion 1:** Identify the image where the robot’s gripper has lifted the `{object}` above the table. There should be a signifcant visible gap between the table and the {object}.
   - **Criterion 2:** The gripper should be actively moving towards the destination, having just completed the pickup phase. Images where the gripper is stationary or moving away from the destination are considered too late.
   - **Criterion 3:** `{object}` must be clearly lifted off the table, ensuring visible space between the table and the object.

**2. End Image Criteria for Deposit:**
   - **Criterion 1:** Locate the image where the gripper has released `{object}` into its designated spot, and the object is visibly settled within the destination. If `{object}` has not been released, the frame is too early.
   - **Criterion 2:** Confirm the presence of preceding images showing `{object}` already in the destination to ensure continuity. Lack of such frames suggests the need for additional footage.
   - **Criterion 3:** Search for images showing a clear retreat of the gripper from the destination. Images where the gripper remains in contact with `{object}` are too early.

**Instruction:**
Evaluate if the first image strictly satisfies the criteria for the START image of this action {action}
Focus on evaluating the first image only.

After reasoning about the answer, return a JSON indicating whether the perfect START image for this action is "perfect" (meaning the perfect image is the first image showed above), "early" (meaning the first image showed above is too early), or "late" (meaning the first image showed above is too late).

Example:  
[Reasoning]
```json
{{
"answer":"perfect"
}}
"""


CHECK_DEPOSIT_END_IMAGE_TIMING = """
### Analyze the Robot's Putting Action: {action}

**Context:**
You are assigned to analyze a sequence in which a robot attempts to deposit an {object} into a destination. The aim is to verify this if the final image FULLY encapsulates the criteria.

**Helpful information:**: 
To check if an object is grasped, check if the robot grippers are holding anything. 
If an object is no longer visible on the table, and is not in the robot's gripper, it means it has been deposited in the destination.
If the action is to place the object in the bin, once deposited you are not able to see the object any more. 
The chopstick is often hard to see, especially when grasped. Please pay special attention if the object is the chopstick.

**1. Start Image Criteria for Deposit:**
   - **Criterion 1:** Identify the image where the robot’s gripper is securely holding `{object}`, which should be elevated and not yet positioned over its final destination. If `{object}` is already positioned over the destination, select an earlier frame as the start.
   - **Criterion 2:** The gripper should be actively moving towards the destination, having just completed the pickup phase. Images where the gripper is stationary or moving away from the destination are considered too late.
   - **Criterion 3:** `{object}` must be clearly lifted off the table, ensuring visible space between the table and the object.

**2. End Image Criteria for Deposit:**
   - **Criterion 1:** Locate the image where the gripper has released `{object}` into its designated spot, and the object is visibly settled within the destination. If `{object}` has not been released, the frame is too early.
   - **Criterion 2:** Confirm the presence of preceding images showing `{object}` already in the destination to ensure continuity. Lack of such frames suggests the need for additional footage.
   - **Criterion 3:** Search for images showing a clear retreat of the gripper from the destination. Images where the gripper remains in contact with `{object}` are too early.

**Instruction:**
Evaluate if the last image strictly satisfies the criteria for the END image of this action {action}
Focus on evaluating the last image only.

After reasoning about the answer, return a JSON indicating whether the perfect END image for this action is "perfect" (meaning its the final image showed above), "early" (meaning the final image showed above is too early), or "late" (meaning the final image showed above is too late).
Think step by step through the criteria. 

Example:  
[Reasoning] 
```json
{{
"answer":"perfect"
}}
"""
