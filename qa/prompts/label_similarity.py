LABEL_SIMILARITY = """
Determine if two task descriptions are similar based on their primary action or object, allowing for some variations in descriptors or specific details.

Examples to guide the comparison:
- 'Pick up glass bowl' and 'Pick up bowl' are considered similar because the primary action ('Pick up') and the main object ('bowl') match.
- 'Put black chopstick into plastic container' and 'Put chopstick into container' are considered similar because both describe the action of putting a chopstick into a container, despite minor differences in descriptors.
- 'Pick up glass bowl' and 'Put down glass bowl', however, are not similar because the primary actions ('Pick up' vs 'Put down') are fundamentally different.
- 'Put chopstick into bin' and 'Put chopstick into container' are not considered similar because the destinations ('bin' vs 'container') differ significantly.

Given two descriptions:
1. Ground Truth Label: "{ground_truth_label}"
2. Prediction Label: "{prediction_label}"

Based on the rules above, determine if these descriptions are similar. Consider descriptions similar if the primary actions and the main objects or destinations are fundamentally the same, even if there are minor differences in how they are described.

If the descriptions are not considered similar, provide a reason based on differences in primary actions or objects.

Return the result and reason as a JSON object:
- A boolean value 'true' indicates the descriptions are sufficiently similar.
- A boolean value 'false' and the reason for this determination indicate the descriptions are not similar.

Expected JSON Output:
{{
  "similar": bool,
  "reason": "optional string explaining why the descriptions are not considered similar, if applicable"
}}

Respond only in a json and nothing else.
"""
