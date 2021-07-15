def get_by_name(name, status):
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


def get_sidecars(spec, appname):
    return [
        container["name"]
        for container in spec["containers"]
        if container["name"] != appname
    ]


def get_running_sidecars(spec, status, appname):
    running_sidecars = []
    for sidecar in get_sidecars(spec, appname):
        sidecar_status = get_by_name(sidecar, status)
        if sidecar_status and get_state(sidecar_status) == "running":
            running_sidecars.append(sidecar)
    return running_sidecars


def get_reason(status):
    if "terminated" in status["state"]:
        return status["state"]["terminated"]["reason"]
    return None


def is_completed(status):
    return "state" in status and get_reason(status) == "Completed"
