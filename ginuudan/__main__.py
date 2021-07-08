import kopf
from kube.port_forward import port_forward
from kube import init_corev1


def get_by_name(name, data):
    if data:
        for d in data:
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


@kopf.on.field(
    "pods",
    annotations={"ginuudan.nais.io/dwindle": "true"},
    field="status.containerStatuses",
)
def judgeme(old, new, name, namespace, spec, **kwargs):
    appname = name.split("-")[0]
    app_container_status = get_by_name(appname, new)
    print(
        f"received container status change for {name} (main container: {appname}). last state: {get_current_state(get_by_name(appname, old))}, new state: {get_current_state(app_container_status)}"
    )
    if not app_container_status:
        return
    if (
        get_current_state(app_container_status) == "terminated"
        and app_container_status["state"]["terminated"]["reason"] == "Completed"
    ):
        print("kill all the sidecars!")
        sidecars = get_sidecars(spec, appname)
        print(sidecars)
        for sidecar in sidecars:
            if sidecar == "linkerd-proxy":
                core_v1 = init_corev1()
                port_forward(name, namespace, 4191, core_v1)
                # use rest-http shutdown
                # port-forward
                continue
            if sidecar == "cloudsql-proxy":
                # use kill -s INT 1
                # exec
                continue
            # ups, can't help you
