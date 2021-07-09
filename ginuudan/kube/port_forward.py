from kubernetes.stream import portforward
import select


def port_forward(api_instance, name, namespace, port, logger):
    pf = portforward(
        api_instance.connect_get_namespaced_pod_portforward,
        name,
        namespace,
        ports=f"{port}",
    )
    http = pf.socket(port)
    http.setblocking(True)
    http.sendall(b"POST /shutdown HTTP/1.1\r\n")
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
    error = pf.error(port)
    if error is None:
        logger.info("Successfully sent shutdown signal.")
    else:
        logger.error("Port 80 has the following error: %s" % error)
