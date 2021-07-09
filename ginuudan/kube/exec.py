from kubernetes.client.rest import ApiException
from kubernetes.stream import stream


def exec_command(api_instance, name, namespace, exec_command, logger):
    try:
        api_instance.read_namespaced_pod(name=name, namespace=namespace)
    except ApiException as e:
        if e.status != 404:
            logger.error("Unknown error: %s" % e)
            return
    resp = stream(
        api_instance.connect_get_namespaced_pod_exec,
        name,
        namespace,
        command=exec_command,
        stderr=True,
        stdin=False,
        stdout=True,
        tty=False,
    )
    logger.info("Response: " + resp)
