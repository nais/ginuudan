def get_by_name(name, status):
    if not status:
        return None
    for d in status:
        if d["name"] == name:
            return d
    return None


def get_current_state(status):
    if status:
        return list(status["state"].keys())[0]
    return None


def get_sidecars(spec, appname):
    return [
        container["name"]
        for container in spec["containers"]
        if container["name"] != appname
    ]
