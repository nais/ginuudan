import kopf
import pathlib

import kube
import actions
import prometheus
import logging

basepath = pathlib.Path(__file__).parent.parent.absolute()  # /!\ hacky alert /!\
actions = actions.load_sidecar_actions(basepath / "actions.yml")

core_v1 = kube.init_corev1()
metrics = prometheus.Metrics()


@kopf.on.startup()
def configure(settings: kopf.OperatorSettings, **_):
    settings.posting.level = logging.WARNING


@kopf.on.field(
    "pods",
    annotations={"ginuudan.nais.io/dwindle": "true"},
    field="status.containerStatuses",
)
def status_change(logger, **kwargs):
    pod = kube.Pod(core_v1, logger=logger, **kwargs)
    event = kube.Event(core_v1)
    if pod.app.name == "":
        logger.warn(f"Required field `labels.app` is not set for {pod.name}")
        return
    if not pod.app.terminated:
        return

    for sidecar in pod.running_sidecars():
        if sidecar not in actions:
            logger.warn(f"I don't know how to shut down {sidecar}")
            event.create(
                f"I don't know how to shut down {sidecar}",
                pod.namespace,
                pod.create_object_reference(),
                'Killing',
                'Warning'
            )
            continue
        logger.info(f"Shutting down {sidecar}")
        action = actions[sidecar]
        if action["type"] == "exec":
            pod.exec_command(sidecar, action["command"].split())
        elif action["type"] == "portforward":
            pod.port_forward(sidecar, action["method"], action["path"], action["port"])
        else:
            logger.warn(f"Unknown action.type `{action['type']}`")
        metrics.sidecars_shutdown_total.labels(
            sidecar, pod.app.name, pod.namespace
        ).inc()
