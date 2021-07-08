import kopf
from kube.port_forward import port_forward
from kube.exec import exec_command
from kube import init_corev1
import spec_utils
import logger


core_v1 = init_corev1()
log = logger.setup_logger("ginuudan")


@kopf.on.field(
    "pods",
    annotations={"ginuudan.nais.io/dwindle": "true"},
    field="status.containerStatuses",
)
def status_change(old, new, name, namespace, spec, **kwargs):
    appname = name.split("-")[0]
    old_app_container_status = spec_utils.get_by_name(appname, old)
    app_container_status = spec_utils.get_by_name(appname, new)

    old_state = spec_utils.get_state(old_app_container_status)
    current_state = spec_utils.get_state(app_container_status)
    log.info(
        f"received container status change for {name} (main container: {appname})."
    )
    log.debug(f"previous state: {old_state},\ncurrent state: {current_state}")
    if not app_container_status:
        return

    if current_state == "terminated" and spec_utils.is_completed(app_container_status):
        sidecars = spec_utils.get_sidecars(spec, appname)
        log.info(
            f"{appname} has reached Completed status. Remaining sidecars: {','.join(sidecars)}"
        )
        for sidecar in sidecars:
            if sidecar == "linkerd-proxy":
                port_forward(name, namespace, 4191, core_v1)
                # use rest-http shutdown
                # port-forward
                continue
            if sidecar == "cloudsql-proxy":
                # use kill -s INT 1
                exec_command(core_v1, name, namespace, ["kill", "-s", "INT", "1"])
                continue
            # ups, can't help you
