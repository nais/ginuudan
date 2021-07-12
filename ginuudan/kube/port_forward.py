from kubernetes.stream import portforward
import select


def port_forward(
    api_instance, name, namespace, http_method, http_path, http_port, logger
):
    pf = portforward(
        api_instance.connect_get_namespaced_pod_portforward,
        name,
        namespace,
        ports=f"{http_port}",
    )
    http = pf.socket(http_port)
    http.setblocking(True)
    http.sendall(bytes(f"{http_method} {http_path} HTTP/1.1\r\n", encoding='ascii'))
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
    logger.debug(response.decode("utf-8"))
    error = pf.error(http_port)
    if error is None:
        logger.info(f"Successfully sent signal to {http_path}.")
    else:
        logger.error(f"Port {http_port} has the following error: {error}")
