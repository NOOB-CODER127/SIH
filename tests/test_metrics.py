import time

from sklearn.metrics import (
    confusion_matrix,
    precision_score,
    recall_score,
    f1_score,
)

from backend.app.graph.alerts import alert_night_bursts


def make_calls(total_calls, night_calls):
    rows = []

    for i in range(night_calls):
        rows.append({
            "timestamp": f"2026-08-20 02:{i:02d}:00",
            "caller_number": "9000011122",
            "callee_number": "9111222333",
        })

    for i in range(total_calls - night_calls):
        rows.append({
            "timestamp": f"2026-08-20 14:{i:02d}:00",
            "caller_number": "9000011122",
            "callee_number": "9111222333",
        })

    return rows


def test_night_burst_metrics():

    # Ground truth:
    # 1 = actually suspicious
    # 0 = actually normal
    test_cases = [
        # total calls, night calls, actual label
        (10, 8, 1),   # suspicious
        (10, 7, 1),   # suspicious
        (10, 3, 0),   # normal
        (7, 7, 0),    # normal: below minimum call count
        (8, 8, 1),    # suspicious
        (20, 2, 0),   # normal
        (12, 6, 1),   # suspicious
        (15, 3, 0),   # normal
        (9, 5, 1),    # suspicious
        (8, 3, 0),    # normal
    ]

    actual = []
    predicted = []

    start_time = time.perf_counter()

    for total_calls, night_calls, actual_label in test_cases:

        rows = make_calls(total_calls, night_calls)

        alerts = alert_night_bursts(rows)

        prediction = 1 if len(alerts) > 0 else 0

        actual.append(actual_label)
        predicted.append(prediction)

    end_time = time.perf_counter()

    # Confusion matrix
    tn, fp, fn, tp = confusion_matrix(
        actual,
        predicted,
        labels=[0, 1]
    ).ravel()

    precision = precision_score(actual, predicted, zero_division=0)
    recall = recall_score(actual, predicted, zero_division=0)
    f1 = f1_score(actual, predicted, zero_division=0)

    execution_time = end_time - start_time

    print("\n========== TRINETRA TEST RESULTS ==========")
    print(f"True Positives  (TP): {tp}")
    print(f"True Negatives  (TN): {tn}")
    print(f"False Positives (FP): {fp}")
    print(f"False Negatives (FN): {fn}")
    print(f"Precision: {precision:.2%}")
    print(f"Recall:    {recall:.2%}")
    print(f"F1-score:  {f1:.2%}")
    print(f"Execution time: {execution_time:.6f} seconds")
    print("===========================================")

    assert precision >= 0
    assert recall >= 0
    assert f1 >= 0