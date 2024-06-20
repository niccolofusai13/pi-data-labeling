
# LABEL_PICKUP_ACTION = """
# ### Analyze the Robot's Pickup Action

# **Action Description:**
# The robot attempts to pick up the object `{object}`. Your task is to identify the precise images where the pickup action starts and ends.

# **Objective:**
# Meticulously determine the exact image numbers marking the start and conclusion of the pickup action involving `{object}`.

# **Instructions:**

# **1. Start Image Criteria for Pickup:**
#    - **Criterion 1:** The robot gripper should not be grasping or holding any objects, including `{object}`
#    - **Criterion 2:** The robot gripper should be about to pick up `{object}`, but has some space in between the gripper and the object.
#    - **Criterion 3:** The gripper should be positioned away from any objects, and the following frames should capture the robot gripper moving towards the `{object}`, before it picks it up. 


# **2. End Image Criteria for Pickup:**
#    - **Criterion 1:** Identify the image where `{object}` is securely held by the gripper and fully lifted off the table. If `{object}` is still touching the table, select a subsequent frame.
#    - **Criterion 2:** Ensure that `{object}` has not yet started moving towards the destination (bin / container). It should have just been picked up, and not yet started its trajectory towards the destination.
   
# **Focus Points:**
#    - Concentrate solely on interactions involving `{object}`.
#    - Ignore any images where the robot interacts with other objects not relevant to the specific pickup action of `{object}`.

# **Expected Deliverables:**
#    - Document the image numbers that correctly represent both the start and end of the pickup action.
#    - Double-check the images against these criteria to ensure accuracy.

# **Sample Response Format:**
# ```json
# {{
#   "start_image": [image number],
#   "end_image": [image number]
# }}
# """


# LABEL_DEPOSIT_ACTION = """
# ### Analyze the Robot's Depositing Action

# **Action Description:**
# The robot is engaged in depositing the object `{object}` into its designated destination. Your task is to identify the precise images where the depositing action begins and ends.

# **Objective:**
# Accurately determine the exact image numbers marking the start and conclusion of the depositing action involving `{object}`.

# **Instructions:**

# **1. Start Image Criteria for Deposit:**
#    - **Criterion 1:** Identify the image where the robot’s gripper is securely holding `{object}`, which should be elevated and not yet positioned over its final destination. If `{object}` is already positioned over the destination, select an earlier frame as the start.
#    - **Criterion 2:** The gripper should be actively moving towards the destination, having just completed the pickup phase. Images where the gripper is stationary or moving away from the destination are considered too late.
#    - **Criterion 3:** `{object}` must be clearly lifted off the table, ensuring visible space between the table and the object.

# **2. End Image Criteria for Deposit:**
#    - **Criterion 1:** Locate the image where the gripper has released `{object}` into its designated spot, and the object is visibly settled within the destination. If `{object}` has not been released, the frame is too early.
#    - **Criterion 2:** Confirm the presence of preceding images showing `{object}` already in the destination to ensure continuity. Lack of such frames suggests the need for additional footage.
#    - **Criterion 3:** Search for images showing a clear retreat of the gripper from the destination. Images where the gripper remains in contact with `{object}` are too early.
#    - **Criterion 4:** The robot gripper should not be picking up the next object.


# **Focus Points:**
#    - Maintain an exclusive focus on interactions involving `{object}`.
#    - Ignore images involving other objects unless they directly impact the depositing action.

# **Expected Deliverables:**
#    - Document the image numbers for both the start and end of the deposit action.
#    - Ensure the images meet the detailed criteria listed above for accurate assessment.

# **Sample Response Format:**
# ```json
# {{
#   "start_image": [image number],
#   "end_image": [image number]
# }}
# """

LABEL_PICKUP_ACTION = """
### Analyze the Robot's Pickup Action

**Action Description:**
The robot attempts to pick up the object `{object}`. Your task is to identify the precise images where the pickup action starts and ends.

**Objective:**
Meticulously determine the exact image numbers marking the start and conclusion of the pickup action involving `{object}`.

**Instructions:**

**1. Start Image Criteria for Pickup:**
   - **Criterion 1:** The robot gripper should not be grasping or holding any objects, including `{object}`
   - **Criterion 2:** The robot gripper should be about to pick up `{object}`, but has some space in between the gripper and the object.
   - **Criterion 3:** The gripper should be positioned away from any objects, and the following frames should capture the robot gripper moving towards the `{object}`, before it picks it up. 

**2. End Image Criteria for Pickup:**
   - **Criterion 1:** Identify the image where `{object}` is securely held by the gripper and fully lifted off the table. If `{object}` is still touching the table, select a subsequent frame.
   - **Criterion 2:** Ensure that `{object}` has not yet started moving towards the destination (bin / container). It should have just been picked up, and not yet started its trajectory towards the destination.
   - **Criterion 3:** The `{object}` should not be over the container / bin yet.
   
**Focus Points:**
   - Concentrate solely on interactions involving `{object}`.
   - Ignore any images where the robot interacts with other objects not relevant to the specific pickup action of `{object}`.

**Expected Deliverables:**
   - Document the image numbers that correctly represent both the start and end of the pickup action.
   - Double-check the images against these criteria to ensure accuracy.

**Sample Response Format:**
```json
{{
  "start_image": [image number],
  "end_image": [image number]
}}
"""


LABEL_DEPOSIT_ACTION = """
### Analyze the Robot's Depositing Action

**Action Description:**
The robot is engaged in depositing the object `{object}` into its designated destination. Your task is to identify the precise images where the depositing action begins and ends.

**Objective:**
Accurately determine the exact image numbers marking the start and conclusion of the depositing action involving `{object}`.

**Instructions:**

**1. Start Image Criteria for Deposit:**
   - **Criterion 1:** Identify the image where the robot’s gripper is securely holding `{object}`, which should be elevated and not yet positioned over its final destination. If `{object}` is already positioned over the destination, select an earlier frame as the start.
   - **Criterion 2:** The gripper should be actively moving towards the destination, having just completed the pickup phase. Images where the gripper is stationary or moving away from the destination are considered too late.
   - **Criterion 3:** `{object}` must be clearly lifted off the table, ensuring visible space between the table and the object.

**2. End Image Criteria for Deposit:**
   - **Criterion 1:** Locate the image where the gripper has released `{object}` into its designated spot, and the object is visibly settled within the destination. If `{object}` has not been released, the frame is too early.
   - **Criterion 2:** Confirm the presence of preceding images showing `{object}` already in the destination to ensure continuity. Lack of such frames suggests the need for additional footage.
   - **Criterion 3:** Search for images showing a clear retreat of the gripper from the destination. Images where the gripper remains in contact with `{object}` are too early.

**Focus Points:**
   - Maintain an exclusive focus on interactions involving `{object}`.
   - Ignore images involving other objects unless they directly impact the depositing action.

**Expected Deliverables:**
   - Document the image numbers for both the start and end of the deposit action.
   - Ensure the images meet the detailed criteria listed above for accurate assessment.

**Sample Response Format:**
```json
{{
  "start_image": [image number],
  "end_image": [image number]
}}
"""

# Relabel frames but start and end frame seperately with even higher FPS
REFINED_START_FRAME_PICK = """
### Analyze the Robot's Pickup Action: {action}

**Context:**
You are assigned to analyze a sequence in which a robot attempts to pick up {object}. The aim is to identify the correct START image that matches the criteria below.

**Helpful information:**: 
To check if an object is grasped, check if the robot grippers are holding anything. 
If an object is no longer visible on the table, and is not in the robot's gripper, it means it has been deposited in the destination.
The black chopstick is often hard to see, especially when grasped. Please pay special attention if the object is the black chopstick.

**Criteria needeed for successful START image for PICK UP:**
- In the first image, the {object} needs to be on the table 
- In the first image, there is some space between the gripper and the {object}
- In the first image, the robot has not yet grasped the object, but is close to.

**Criteria needeed for successful END image for picking up:**
- In the final image, the {object} has been lifted off the table, enough to see space between the object and the table.
- In the final image, the {object} is grasped by the robot

**Instruction:**
From the images above, which image best describes the START image criteria above.

After reasoning about the answer, return a JSON for your answer with a number associated to the image that best matches the START image from the ones above.
Example:  
```json
{{
"answer":3
}}
"""


REFINED_END_FRAME_PICK = """
### Analyze the Robot's Pickup Action: {action}

**Context:**
You are assigned to analyze a sequence in which a robot attempts to pick up {object}. The aim is to identify the correct END image that matches the criteria below.

**Helpful information:**: 
To check if an object is grasped, check if the robot grippers are holding anything. 
If an object is no longer visible on the table, and is not in the robot's gripper, it means it has been deposited in the destination.
The black chopstick is often hard to see, especially when grasped. Please pay special attention if the object is the black chopstick.

**Criteria needeed for successful START image for PICK UP:**
- In the first image, the {object} needs to be on the table 
- In the first image, there is some space between the gripper and the {object}
- In the first image, the robot has not yet grasped the object, but is close to.

**Criteria needeed for successful END image for picking up:**
- In the final image, the {object} has been lifted off the table, enough to see space between the object and the table.
- In the final image, the {object} is grasped by the robot

**Instruction:**
From the images above, which image best describes the END image criteria above.

After reasoning about the answer, return a JSON for your answer with a number associated to the image that best matches the END image from the ones above.
Example:  
```json
{{
"answer": 9
}}
"""


REFINED_START_FRAME_DEPOSIT = """
### Analyze the Robot's Putting Action: {action}

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
- In the final image, the robot gripper has retreated 


**Instruction:**
From the images above, which image best describes the START image criteria above.

After reasoning about the answer, return a JSON for your answer with a number associated to the image that best matches the START image from the ones above.
Example:  
```json
{{
"answer":3
}}
"""


REFINED_END_FRAME_DEPOSIT = """
### Analyze the Robot's Putting Action: {action}

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
- In the final image, the robot gripper has retreated 

**Instruction:**
From the images above, which image best describes the END image criteria above.

After reasoning about the answer, return a JSON for your answer with a number associated to the image that best matches the END image from the ones above.
Example:  
```json
{{
"answer": 9
}}

"""
