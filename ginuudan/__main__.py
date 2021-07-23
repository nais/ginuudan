import kopf
import pathlib

import kube
import actions
import prometheus

basepath = pathlib.Path(__file__).parent.parent.absolute()  # /!\ hacky alert /!\
actions = actions.load_sidecar_actions(basepath / "actions.yml")

core_v1 = kube.init_corev1()
metrics = prometheus.Metrics()


@kopf.on.field(
    "pods",
    annotations={"ginuudan.nais.io/dwindle": "true"},
    field="status.containerStatuses",
)
def status_change(logger, **kwargs):
    pod = kube.Pod(core_v1, logger=logger, **kwargs)
    if pod.app.name == "":
        logger.warn(f"Required field `labels.app` is not set for {pod.name}")
        return
    if not pod.app.terminated:
        return

    for sidecar in pod.running_sidecars():
        if sidecar not in actions:
            logger.warn(f"I don't know how to shut down {sidecar}")
            continue
        logger.info(f"Shutting down {sidecar}")
        action = actions[sidecar]
        if action["type"] == "exec":
            pod.exec_command(sidecar, action["command"].split())
        elif action["type"] == "portforward":
            pod.port_forward(action["method"], action["path"], action["port"])
        else:
            logger.warn(f"Unknown action.type `{action['type']}`")
        metrics.sidecars_shutdown_total.labels(
            sidecar, pod.app.name, pod.namespace
        ).inc()
