import kopf
from kube.port_forward import port_forward
from kube.exec import exec_command
from kube import init_corev1
import spec_utils


core_v1 = init_corev1()


@kopf.on.field(
    "pods",
    annotations={"ginuudan.nais.io/dwindle": "true"},
    field="status.containerStatuses",
)
def status_change(old, new, name, namespace, spec, status, logger, **kwargs):
    appname = name.split("-")[0]
    if status["phase"] == "Succeeded":
        return

    old_app_container_status = spec_utils.get_by_name(appname, old)
    app_container_status = spec_utils.get_by_name(appname, new)
    if not app_container_status:
        return

    old_state = spec_utils.get_state(old_app_container_status)
    current_state = spec_utils.get_state(app_container_status)
    logger.info(
        f"Status change for {name} (main container: {appname}): Old: {old_state}, new: {current_state}"
    )

    if current_state == "terminated" and spec_utils.is_completed(app_container_status):
        sidecars = spec_utils.get_sidecars(spec, appname)
        logger.info(
            f"{appname} has reached Completed status. Remaining sidecars: {','.join(sidecars)}"
        )
        for sidecar in sidecars:
            if sidecar == "linkerd-proxy":
                logger.info("Shutting down linkerd-proxy")
                port_forward(
                    core_v1, name, namespace, "POST", "/shutdown", 4191, logger
                )
            if sidecar == "cloudsql-proxy":
                logger.info("Shutting down cloudsql-proxy")
                cmd = ["kill", "-s", "INT", "1"]
                exec_command(core_v1, name, namespace, cmd, logger)
