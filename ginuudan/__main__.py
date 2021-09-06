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
event = kube.Event(core_v1)


@kopf.on.startup()
def configure(settings: kopf.OperatorSettings, **_):
    settings.posting.enabled = False


@kopf.on.field(
    "pods",
    annotations={"ginuudan.nais.io/dwindle": "true"},
    field="status.containerStatuses",
)
def status_change(logger, **kwargs):
    pod = kube.Pod(core_v1, logger=logger, **kwargs)
    if pod.app.name == "":
        event.create(
            f"Required field `labels.app` is not set",
            pod.namespace,
            pod.create_object_reference(),
            "Killing",
            "Error",
        )
        return
    if not pod.app.terminated:
        return

    for sidecar in pod.running_sidecars():
        if sidecar not in actions:
            logger.error(f"I don't know how to shut down {sidecar}")
            event.create(
                f"I don't know how to shut down {sidecar}",
                pod.namespace,
                pod.create_object_reference(),
                "Killing",
                "Error",
            )
            continue
        logger.info(f"Shutting down {sidecar}")
        event.create(
            f"Shutting down {sidecar}",
            pod.namespace,
            pod.create_object_reference(),
            "Killing",
        )
        action = actions[sidecar]
        if action["type"] == "exec":
            pod.exec_command(sidecar, action["command"].split())
        elif action["type"] == "portforward":
            pod.port_forward(sidecar, action["method"], action["path"], action["port"])
        else:
            logger.error(f"Unknown action.type `{action['type']}`")
        metrics.sidecars_shutdown_total.labels(
            sidecar, pod.app.name, pod.namespace
        ).inc()
