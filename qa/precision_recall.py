def calculate_tp_fp_fn(gt, pred):
    gt_start, gt_end = gt["start_frame"], gt["end_frame"]
    pred_start, pred_end = pred["start_frame"], pred["end_frame"]

    # True Positive (TP): Overlapping frames
    overlap_start = max(gt_start, pred_start)
    overlap_end = min(gt_end, pred_end)
    tp = max(0, overlap_end - overlap_start)

    # False Positive (FP): Predicted frames not in ground truth
    fp = (pred_end - pred_start) - tp

    # False Negative (FN): Ground truth frames not predicted
    fn = (gt_end - gt_start) - tp

    return tp, fp, fn


def calculate_precision(tp, fp):
    if tp + fp == 0:
        return 0.0
    return tp / (tp + fp)


def calculate_recall(tp, fn):
    if tp + fn == 0:
        return 0.0
    return tp / (tp + fn)


def calculate_weighted_metric(
    precision, recall, precision_weight=0.4, recall_weight=0.6
):
    return (precision_weight * precision) + (recall_weight * recall)


def calculate_episode_precision_recall(gt, pred):

    tp, fp, fn = calculate_tp_fp_fn(gt, pred)

    precision = calculate_precision(tp, fp)
    recall = calculate_recall(tp, fn)
    return precision, recall


def calculate_average_precision_recall(episodes_ground_truth, episodes_predictions):
    total_precision, total_recall, num_episodes = 0, 0, 0

    for gt, pred in zip(episodes_ground_truth, episodes_predictions):
        precision, recall = calculate_episode_precision_recall(gt, pred)
        total_precision += precision
        total_recall += recall
        num_episodes += 1

    avg_precision = total_precision / num_episodes
    avg_recall = total_recall / num_episodes

    return avg_precision, avg_recall
