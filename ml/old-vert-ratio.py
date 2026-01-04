def get_vertical_ratio(lm, w, h):
    # Indices: Top, Bottom, Iris
    # Right Eye: 159 (Top), 145 (Bottom), 468 (Iris)
    # Left Eye:  386 (Top), 374 (Bottom), 473 (Iris)

    def v_ratio(top_idx, bot_idx, iris_idx):
        top, bot, iris = lm[top_idx], lm[bot_idx], lm[iris_idx]
        eye_height = math.hypot((top.x - bot.x) * w, (top.y - bot.y) * h)
        dist_top = math.hypot((top.x - iris.x) * w, (top.y - iris.y) * h)
        # Avoid division by zero (blinking)
        return dist_top / eye_height if eye_height > 2.0 else 0.5

    r_vert = v_ratio(159, 145, 468)
    l_vert = v_ratio(386, 374, 473)
    return (r_vert + l_vert) / 2