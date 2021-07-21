from kubernetes import config
from kubernetes.client import Configuration
from kubernetes.client.api import core_v1_api
from kubernetes.client.rest import ApiException
from kubernetes.stream import stream, portforward
import select
import utils


def init_corev1():
    config.load_kube_config()
    c = Configuration.get_default_copy()
    c.assert_hostname = False
    Configuration.set_default(c)
    return core_v1_api.CoreV1Api()


class App:
    def __init__(self, labels=None, new=None):
        self.name = labels["app"] if "app" in labels else ""
        self.status = utils.get_status_for(new, self.name)
        self.state = utils.get_state(self.status)

    @property
    def terminated(self):
        return self.state == "terminated"


class Pod:
    def __init__(
        self,
        core_v1,
        labels=None,
        logger=None,
        name=None,
        namespace=None,
        new=None,
        spec=None,
        **kwargs,
    ):
        self.core_v1 = core_v1
        self.name = name
        self.namespace = namespace
        self.logger = logger
        self.spec = spec
        self.new = new
        self.app = App(labels, new)

    def __sidecars(self):
        return [
            container["name"]
            for container in self.spec["containers"]
            if container["name"] != self.app.name
        ]

    def running_sidecars(self):
        for sidecar in self.__sidecars():
            sidecar_status = utils.get_status_for(self.new, sidecar)
            if utils.get_state(sidecar_status) == "running":
                yield sidecar

    def exec_command(self, container, command):
        try:
            self.core_v1.read_namespaced_pod(name=self.name, namespace=self.namespace)
        except ApiException as e:
            if e.status != 404:
                self.logger.error("Unknown error: %s" % e)
                return
        resp = stream(
            self.core_v1.connect_get_namespaced_pod_exec,
            self.name,
            self.namespace,
            container=container,
            command=command,
            stderr=True,
            stdin=False,
            stdout=True,
            tty=False,
        )
        self.logger.info("Response: " + resp)
        # TODO: return whether the exec succeeded

    def port_forward(self, method, path, port):
        pf = portforward(
            self.core_v1.connect_get_namespaced_pod_portforward,
            self.name,
            self.namespace,
            ports=f"{port}",
        )
        http = pf.socket(port)
        http.setblocking(True)
        http.sendall(bytes(f"{method} {path} HTTP/1.1\r\n", encoding="ascii"))
        http.sendall(b"Host: 127.0.0.1\r\n")
        http.sendall(b"Connection: close\r\n")
        http.sendall(b"Accept: */*\r\n")
        http.sendall(b"\r\n")
        response = b""
        while True:
            select.select([http], [], [])
            data = http.recv(1024)
            if not data:
                break
            response += data
        http.close()
        self.logger.debug(f"Response: {response.decode('utf-8')}")
        error = pf.error(port)
        if error is None:
            self.logger.info(f"Successfully sent signal to {path}.")
        else:
            self.logger.error(f"Port {port} has the following error: {error}")
        # error can be used to return whether port forward succeeded,
        # but perhaps we should raise exceptions instead
