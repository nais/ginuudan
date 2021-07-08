from kubernetes.stream import portforward
import select
import socket
from urllib import request


def port_forward(name, namespace, port, api_instance):
    pf = portforward(
        api_instance.connect_get_namespaced_pod_portforward,
        name,
        namespace,
        ports=str(port),
    )
    http = pf.socket(port)
    http.setblocking(True)
    http.sendall(b"GET / HTTP/1.1\r\n")
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
    print(response.decode("utf-8"))
    error = pf.error(port)
    if error is None:
        print(f"No port forward errors on port {port}.")
    else:
        print(f"Port {port} has the following error: {error}")

    # Monkey patch socket.create_connection which is used by http.client and
    # urllib.request. The same can be done with urllib3.util.connection.create_connection
    # if the "requests" package is used.
    socket_create_connection = socket.create_connection

    def kubernetes_create_connection(address, *args, **kwargs):
        dns_name = address[0]
        if isinstance(dns_name, bytes):
            dns_name = dns_name.decode()
        dns_name = dns_name.split(".")
        if dns_name[-1] != "kubernetes":
            return socket_create_connection(address, *args, **kwargs)
        if len(dns_name) not in (3, 4):
            raise RuntimeError("Unexpected kubernetes DNS name.")
        namespace = dns_name[-2]
        name = dns_name[0]
        port = address[1]
        if len(dns_name) == 4:
            if dns_name[1] in ("svc", "service"):
                service = api_instance.read_namespaced_service(name, namespace)
                for service_port in service.spec.ports:
                    if service_port.port == port:
                        port = service_port.target_port
                        break
                else:
                    raise RuntimeError("Unable to find service port: %s" % port)
                label_selector = []
                for key, value in service.spec.selector.items():
                    label_selector.append("%s=%s" % (key, value))
                pods = api_instance.list_namespaced_pod(
                    namespace, label_selector=",".join(label_selector)
                )
                if not pods.items:
                    raise RuntimeError("Unable to find service pods.")
                name = pods.items[0].metadata.name
                if isinstance(port, str):
                    for container in pods.items[0].spec.containers:
                        for container_port in container.ports:
                            if container_port.name == port:
                                port = container_port.container_port
                                break
                        else:
                            continue
                        break
                    else:
                        raise RuntimeError(
                            "Unable to find service port name: %s" % port
                        )
            elif dns_name[1] != "pod":
                raise RuntimeError("Unsupported resource type: %s" % dns_name[1])
        pf = portforward(
            api_instance.connect_get_namespaced_pod_portforward,
            name,
            namespace,
            ports=str(port),
        )
        return pf.socket(port)

    socket.create_connection = kubernetes_create_connection

    # Access the nginx http server using the
    # "<pod-name>.pod.<namespace>.kubernetes" dns name.
    # response = urllib_request.urlopen(
    req = request.Request(
        f"http://{name}.pod.{namespace}.kubernetes/shutdown", method="POST"
    )
    resp = request.urlopen(req)
    html = resp.read().decode("utf-8")
    resp.close()
    print("Status Code: {resp.code}")
    print(html)
