
# PICKUP_BEFORE_AFTER_START_PROMPT = """
# ### Analyze the Robot's Pickup Task: {action}

# **Context:**
# You are assigned to analyze a sequence in which a robot attempts to pick up {object}. The aim is to verify this if the first image FULLY encapsulates the criteria.

# **Helpful information:**: 
# To check if an object is grasped, check if the robot grippers are holding anything. 
# If an object is no longer visible on the table, and is not in the robot's gripper, it means it has been deposited in the destination.
# The black chopstick is often hard to see, especially when grasped. Please pay special attention if the object is the black chopstick.

# **Criteria needeed for successful START image for PICK UP:**
# - In the first image, the {object} needs to be on the table 
# - In the first image, there is some space between the gripper and the {object}
# - In the first image, the robot has not yet grasped the object

# **Criteria needeed for successful END image for picking up:**
# - In the final image, the {object} has been lifted off the table, enough to see space between the object and the table.
# - In the final image, the {object} is grasped by the robot

# **Instruction:**
# Evaluate if the first image strictly satisfies the criteria for the START image of this action {action}? 
# Focus on evaluating the first image only.

# After reasoning about the answer, return a JSON indicating whether the perfect START image for this task is "perfect" (meaning the perfect image is the first image showed above), "before" (meaning the ideal START image is before in the video), or "after" (meaning the ideal START image is further in the video).

# Example:  
# {{
# "answer":"perfect"
# }}
# """

# PICKUP_BEFORE_AFTER_END_PROMPT = """
# ### Analyze the Robot's Pickup Task: {action}

# **Context:**
# You are assigned to analyze a sequence in which a robot attempts to pick up {object}. The aim is to verify this if the final image FULLY encapsulates the criteria.

# **Helpful information:**: 
# To check if an object is grasped, check if the robot grippers are holding anything. 
# If an object is no longer visible on the table, and is not in the robot's gripper, it means it has been deposited in the destination.
# The black chopstick is often hard to see, especially when grasped. Please pay special attention if the object is the black chopstick.

# **Criteria needeed for successful START image for PICK UP:**
# - In the first image, the {object} needs to be on the table 
# - In the first image, there is some space between the gripper and the {object}
# - In the first image, the robot gripper has to be empty and not grasping any object yet

# **Criteria needeed for successful END image for picking up:**
# - In the final image, the {object} has been lifted off the table, enough to see space between the object and the table.
# - In the final image, the {object} is grasped by the robot

# **Instruction:**
# Evaluate if the last image strictly satisfies the criteria for the END image of this action {action}? 
# Focus on evaluating the last image only.

# After reasoning about the answer, return a JSON indicating whether the perfect END image for this task is "perfect" (meaning its the final image showed above), "before" (meaning the ideal END image is before in the video), or "after" (meaning the ideal END image is further in the video).

# Example:  
# {{
# "answer":"perfect"
# }}
# """


# DEPOSIT_BEFORE_AFTER_START_PROMPT = """
# ### Analyze the Robot's Putting Task: {action}

# **Context:**
# You are assigned to analyze a sequence in which a robot attempts to deposit an {object} into a destination. The aim is to verify this if the first image FULLY encapsulates the criteria.

# **Helpful information:**: 
# To check if an object is grasped, check if the robot grippers are closed and holding the object. 
# If an object is no longer visible on the table, and is not in the robot's gripper, it means it has been deposited in the destination.
# The black chopstick is often hard to see, especially when grasped. Please pay special attention if the object is the black chopstick.

# **Criteria needeed for successful START image for depositing an object:**
# - In the first image, the {object} needs to be *starting* lifted above the table (to any degree).
# - In the first image, the {object} needs to be not have been released yet.

# **Criteria needeed for successful END image for depositing an object:**
# - In the final image, the {object} is no longer airborn. 
# - In the final image, the {object} was placed into one of the bin or plastic container

# **Instruction:**
# Evaluate if the first image strictly satisfies the criteria for the START image of this action {action}? 
# Focus on evaluating the first image only.

# After reasoning about the answer, return a JSON indicating whether the perfect START image for this task is "perfect" (meaning the perfect image is the first image showed above), "before" (meaning the ideal START image is before in the video), or "after" (meaning the ideal START image is further in the video).

# Example:  
# {{
# "answer":"perfect"
# }}
# """


# DEPOSIT_BEFORE_AFTER_END_PROMPT = """
# ### Analyze the Robot's Putting Task: {action}

# **Context:**
# You are assigned to analyze a sequence in which a robot attempts to deposit an {object} into a destination. The aim is to verify this if the final image FULLY encapsulates the criteria.

# **Helpful information:**: 
# To check if an object is grasped, check if the robot grippers are holding anything. 
# If an object is no longer visible on the table, and is not in the robot's gripper, it means it has been deposited in the destination.
# If the task is to place the object in the bin, once deposited you are not able to see the object any more. 
# The black chopstick is often hard to see, especially when grasped. Please pay special attention if the object is the black chopstick.

# **Criteria needeed for successful START image for depositing an object:**
# - In the first image, the {object} needs to be *starting* lifted above the table (to any degree).
# - In the first image, the {object} needs to be not have been released yet.

# **Criteria needeed for successful END image for depositing an object:**
# - In the final image, the {object} is no longer airborn. 
# - In the final image, the {object} was placed into one of the bin or plastic container

# **Instruction:**
# Evaluate if the last image strictly satisfies the criteria for the END image of this action {action}? 
# Focus on evaluating the last image only.

# After reasoning about the answer, return a JSON indicating whether the perfect END image for this task is "perfect" (meaning its the final image showed above), "before" (meaning the ideal END image is before in the video), or "after" (meaning the ideal END image is further in the video).
# Example:  
# {{
# "answer":"perfect"
# }}
# """


































































PICKUP_BEFORE_AFTER_START_PROMPT = """
### Analyze the Robot's Pickup Task: {action}

**Context:**
You are assigned to analyze a sequence in which a robot attempts to pick up {object}. The aim is to verify this if the first image FULLY encapsulates the criteria.

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
Evaluate if the first image strictly satisfies the criteria for the START image of this action {action}? 
Focus on evaluating the first image only.

After reasoning about the answer, return a JSON indicating whether the perfect START image for this task is "perfect" (meaning the perfect image is the first image showed above), "early" (meaning the first image showed above is too early), or "late" (meaning the first image showed above is too late).

Example:  
{{
"answer":"perfect"
}}
"""

PICKUP_BEFORE_AFTER_END_PROMPT = """
### Analyze the Robot's Pickup Task: {action}

**Context:**
You are assigned to analyze a sequence in which a robot attempts to pick up {object}. The aim is to verify this if the final image FULLY encapsulates the criteria.

**Helpful information:**: 
To check if an object is grasped, check if the robot grippers are holding anything. 
If an object is no longer visible on the table, and is not in the robot's gripper, it means it has been deposited in the destination.
The black chopstick is often hard to see, especially when grasped. Please pay special attention if the object is the black chopstick.

**Criteria needeed for successful START image for PICK UP:**
- In the first image, the {object} needs to be on the table 
- In the first image, there is some space between the gripper and the {object}
- In the first image, the robot gripper has to be empty and not grasping any object yet

**Criteria needeed for successful END image for picking up:**
- In the final image, the {object} has been lifted off the table, enough to see space between the object and the table.
- In the final image, the {object} is grasped by the robot

**Instruction:**
Evaluate if the last image strictly satisfies the criteria for the END image of this action {action}? 
Focus on evaluating the last image only.

After reasoning about the answer, return a JSON indicating whether the perfect END image for this task is "perfect" (meaning its the final image showed above), "early" (meaning the final image showed above is too early), or "late" (meaning the final image showed above is too late).

Example:  
{{
"answer":"perfect"
}}
"""


DEPOSIT_BEFORE_AFTER_START_PROMPT = """
### Analyze the Robot's Putting Task: {action}

**Context:**
You are assigned to analyze a sequence in which a robot attempts to deposit an {object} into a destination. The aim is to verify this if the first image FULLY encapsulates the criteria.

**Helpful information:**: 
To check if an object is grasped, check if the robot grippers are closed and holding the object. 
If an object is no longer visible on the table, and is not in the robot's gripper, it means it has been deposited in the destination.
The black chopstick is often hard to see, especially when grasped. Please pay special attention if the object is the black chopstick.

**Criteria needeed for successful START image for depositing an object:**
- In the first image, the {object} needs to be *starting* lifted above the table (to any degree).
- In the first image, the {object} needs to be not have been released yet.

**Criteria needeed for successful END image for depositing an object:**
- In the final image, the {object} is no longer airborn. 
- In the final image, the {object} was placed into one of the bin or plastic container

**Instruction:**
Evaluate if the first image strictly satisfies the criteria for the START image of this action {action}? 
Focus on evaluating the first image only.

After reasoning about the answer, return a JSON indicating whether the perfect START image for this task is "perfect" (meaning the perfect image is the first image showed above), "early" (meaning the first image showed above is too early), or "late" (meaning the first image showed above is too late).

Example:  
{{
"answer":"perfect"
}}
"""


DEPOSIT_BEFORE_AFTER_END_PROMPT = """
### Analyze the Robot's Putting Task: {action}

**Context:**
You are assigned to analyze a sequence in which a robot attempts to deposit an {object} into a destination. The aim is to verify this if the final image FULLY encapsulates the criteria.

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
Evaluate if the last image strictly satisfies the criteria for the END image of this action {action}? 
Focus on evaluating the last image only.

After reasoning about the answer, return a JSON indicating whether the perfect END image for this task is "perfect" (meaning its the final image showed above), "early" (meaning the final image showed above is too early), or "late" (meaning the final image showed above is too late).
Example:  
{{
"answer":"perfect"
}}
"""



"""
------------------------------------------------------------------------------------------------------------------------------------------------
"""



START_FRAME_PICK_ESTIMATE = """
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
{{
"answer":3
}}
"""


END_FRAME_PICK_ESTIMATE = """
### Analyze the Robot's Putting Task: {action}

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
{{
"answer": 9
}}
"""


START_FRAME_PUT_ESTIMATE = """
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
{{
"answer":3
}}
"""


END_FRAME_PUT_ESTIMATE = """
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
{{
"answer": 9
}}

"""


