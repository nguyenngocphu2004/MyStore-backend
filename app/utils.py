from datetime import datetime


def time_ago(dt):
    now = datetime.now()
    diff = now - dt
    seconds = diff.total_seconds()

    if seconds < 60:
        return f"{int(seconds)} giây trước"
    elif seconds < 3600:
        return f"{int(seconds // 60)} phút trước"
    elif seconds < 86400:
        return f"{int(seconds // 3600)} giờ trước"
    elif seconds < 2592000:
        return f"{int(seconds // 86400)} ngày trước"
    else:
        return dt.strftime("%Y-%m-%d")

