from openai import OpenAI 
from config import OPENAI_API_KEY, MODEL
from prompts.label_similarity import LABEL_SIMILARITY
from video_labeling.utils import extract_json_from_response


client = OpenAI(api_key=OPENAI_API_KEY)

def get_midpoint_frame(label):
    return (label['start_frame'] + label['end_frame']) // 2

def get_label_for_predicted_frame(frame, predictions):
    for prediction in predictions:
        if prediction['start_frame'] <= frame <= prediction['end_frame']:
            return prediction['task_name']
    return None


def labels_are_similar(ground_truth_label, prediction_label):

    prompt = LABEL_SIMILARITY.format(ground_truth_label=ground_truth_label, prediction_label=prediction_label)
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "user", "content": 
                prompt
        }
        ],
        temperature=0,
    )


    response = response.choices[0].message.content
    response = extract_json_from_response(response)

    return response['similar']
    
def calculate_label_accuracy(ground_truth, predictions):
    correct_count = 0
    incorrect_pairs = []
    
    for gt in ground_truth:
        mid_frame = get_midpoint_frame(gt)
        pred = get_label_for_predicted_frame(mid_frame, predictions)
        if pred and  labels_are_similar(gt['task_name'], pred):
            correct_count += 1
        else:
            incorrect_pairs.append((gt, pred))
    
    accuracy = correct_count / len(ground_truth) if ground_truth else 0
    return accuracy, incorrect_pairs


