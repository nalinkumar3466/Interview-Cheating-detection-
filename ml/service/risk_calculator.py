def compute_effective_risk_percentage(event_percentages):
    """
    Prevent overlap inflation by taking the MAX suspicious exposure.
    """
    if not event_percentages:
        return 0.0

    return max(e["percentage_in_video"] for e in event_percentages)


def classify_risk_level(effective_percentage):
    """
    Risk calibration thresholds.
    """
    if effective_percentage < 15:
        return "Low"
    elif effective_percentage <= 35:
        return "Medium"
    else:
        return "High"
