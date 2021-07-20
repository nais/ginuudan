import kopf
import pathlib

import kube
import actions

basepath = pathlib.Path(__file__).parent.parent.absolute()  # /!\ hacky alert /!\
actions = actions.load_sidecar_actions(basepath / "actions.yml")
core_v1 = kube.init_corev1()


@kopf.on.field(
    "pods",
    annotations={"ginuudan.nais.io/dwindle": "true"},
    field="status.containerStatuses",
)
def status_change(logger, status, labels, **kwargs):
    if status["phase"] in ["Succeeded", "Failed"]:
        return
    if not "app" in labels:
        return

    handler = kube.KubernetesHandler(core_v1, logger=logger, labels=labels, **kwargs)

    if not handler.app_status:
        return
    if not handler.completed:
        return

    sidecars = handler.running_sidecars
    logger.info(
        f"{handler.app_name} has reached Completed status. Remaining sidecars: {','.join(sidecars)}"
    )
    for sidecar in sidecars:
        if sidecar in actions:
            logger.info(f"Shutting down {sidecar}")
            action = actions[sidecar]
            if action["type"] == "exec":
                handler.exec_command(sidecar, action["command"].split())
            elif action["type"] == "portforward":
                handler.port_forward(action["method"], action["path"], action["port"])
        else:
            logger.warn(f"I don't know how to shut down {sidecar}")
