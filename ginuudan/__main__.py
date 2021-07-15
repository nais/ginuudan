import kopf
from kube import init_corev1, KubernetesHandler
import utils
import actions

actions = actions.load_sidecar_actions()
core_v1 = init_corev1()


@kopf.on.field(
    "pods",
    annotations={"ginuudan.nais.io/dwindle": "true"},
    field="status.containerStatuses",
)
def status_change(new, name, namespace, labels, spec, status, logger, **kwargs):
    if status["phase"] in ["Succeeded", "Failed"]:
        return
    if not "app" in labels:
        return

    appname = labels["app"]
    app_status = utils.get_by_name(appname, new)
    if not app_status:
        return

    if utils.get_state(app_status) == "terminated" and utils.is_completed(app_status):
        handler = KubernetesHandler(core_v1, name, namespace, logger)
        sidecars = utils.get_running_sidecars(spec, new, appname)
        logger.info(
            f"{appname} has reached Completed status. Remaining sidecars: {','.join(sidecars)}"
        )
        for sidecar in sidecars:
            if sidecar in actions:
                logger.info(f"Shutting down {sidecar}")
                action = actions[sidecar]
                if action["type"] == "exec":
                    handler.exec_command(action["command"].split())
                elif action["type"] == "portforward":
                    handler.port_forward(
                        action["method"], action["path"], action["port"]
                    )
            else:
                logger.warn(f"I don't know how to shut down {sidecar}")
