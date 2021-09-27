import kopf
import pathlib

import kube
import actions
import prometheus

basepath = pathlib.Path(__file__).parent.parent.absolute()  # /!\ hacky alert /!\
actions = actions.load_sidecar_actions(basepath / "actions.yml")
nuclear = True

core_v1 = kube.init_corev1()
metrics = prometheus.Metrics()
pod_event = kube.Event(core_v1, nuclear=nuclear)


@kopf.on.startup()
def configure(settings: kopf.OperatorSettings, **_):
    settings.posting.enabled = False

if nuclear:
    print("Running nuclear mode. Events will not be posted to pods,")
    @kopf.on.event(
        "pods",
        annotations={"ginuudan.nais.io/dwindle": "true"},
    )
    def event_change(event, logger, **kwargs):
        containerStatuses = event['object']['status']['containerStatuses']
        pod = kube.Pod(core_v1, pod_event, containerStatuses, logger=logger, **kwargs)
        if pod.app.name == "":
            return
        if not pod.app.terminated:
            return

        for sidecar in pod.running_sidecars():
            if sidecar not in actions:
                logger.error(f"I don't know how to shut down {sidecar}")
                continue
            logger.info(f"Shutting down {sidecar}")
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
else:
    @kopf.on.field(
        "pods",
        annotations={"ginuudan.nais.io/dwindle": "true"},
        field="status.containerStatuses",
    )
    def status_change(status, logger, **kwargs):
        containerStatuses = status["containerStatuses"]
        pod = kube.Pod(core_v1, pod_event, containerStatuses, logger=logger, **kwargs)
        if pod.app.name == "":
            pod_event.error(pod, f"Required field `labels.app` is not set")
            return
        if not pod.app.terminated:
            return

        for sidecar in pod.running_sidecars():
            if sidecar not in actions:
                logger.error(f"I don't know how to shut down {sidecar}")
                pod_event.error(pod, f"I don't know how to shut down {sidecar}")
                continue
            logger.info(f"Shutting down {sidecar}")
            pod_event.normal(pod, f"Shutting down {sidecar}")
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