def get_status_for(status, name):
    if not status:
        return None
    for d in status:
        if d["name"] == name:
            return d
    return None


def get_state(status):
    if status:
        return list(status["state"].keys())[0]
    return None
