def determine_error_type(predicted_frame, true_frame, system_fps, video_fps=30, window_size=2):
    """
    Calculate error between predicted and true frame numbers with consideration for frame rate differences.
    """
    frames_per_system_frame = video_fps / system_fps
    acceptable_difference = frames_per_system_frame * window_size
    frame_difference = abs(predicted_frame - true_frame)

    if frame_difference <= acceptable_difference:
        return 'fine'
    elif frame_difference <= 2 * acceptable_difference:
        return 'minor'
    else:
        return 'major'

def check_episode_error(episode_prediction, episode_ground_truth, system_fps):
    start_frame_error = determine_error_type(episode_prediction['start_frame'], episode_ground_truth['start_frame'], system_fps)
    end_frame_error = determine_error_type(episode_prediction['end_frame'], episode_ground_truth['end_frame'], system_fps)
    
    return start_frame_error, end_frame_error


def errors_within_accepted_range(ground_truth_labels, predictions):
    minor_count = 0
    major_count = 0
    system_fps = 2

    if len(predictions) != len(ground_truth_labels):
        print("Mismatch in the number of predictions and ground truth labels.")
        return False

    for idx, prediction in enumerate(predictions):
        ground_truth = ground_truth_labels[idx]
        
        start_frame_error, end_frame_error = check_episode_error(prediction, ground_truth, system_fps)
        print(f"Episode {idx}: Start Frame Error - {start_frame_error}, End Frame Error - {end_frame_error}")

        if 'major' in [start_frame_error, end_frame_error]:
            major_count += 1
            print(f"Major error found in Episode {idx}. Failing validation.")
            return False 
        
        minor_count += [start_frame_error, end_frame_error].count('minor')

    if minor_count > 2:
        print(f"Exceeded allowable minor error count with {minor_count} minor errors. Failing validation.")
        return False
    
    print(f"Validation passed with {minor_count} minor errors and {major_count} major errors.")
    return True
