import kopf
from kube.port_forward import port_forward
from kube import init_corev1
from spec import get_by_name, get_current_state, get_sidecars
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
    old_app_container_status = get_by_name(appname, old)
    app_container_status = get_by_name(appname, new)
    log.info(
        f"""received container status change for {name} (main container: {appname}).
        last state: {get_current_state(old_app_container_status)}, 
        new state:  {get_current_state(app_container_status)}
        """
    )
    if not app_container_status:
        return
    if (
        get_current_state(app_container_status) == "terminated"
        and app_container_status["state"]["terminated"]["reason"] == "Completed"
    ):
        sidecars = get_sidecars(spec, appname)
        log.info(
            f"""{appname} has reached Completed status.
            Remaining sidecars: {','.join(sidecars)}
            """
        )
        for sidecar in sidecars:
            if sidecar == "linkerd-proxy":
                port_forward(name, namespace, 4191, core_v1)
                # use rest-http shutdown
                # port-forward
                continue
            if sidecar == "cloudsql-proxy":
                # use kill -s INT 1
                # exec
                continue
            # ups, can't help you
