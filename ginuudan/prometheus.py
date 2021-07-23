import prometheus_client as prometheus


class Metrics:
    def __init__(self):
        prometheus.start_http_server(9090)
        self.sidecars_shutdown_total = prometheus.Counter(
            "sidecars_shutdown_total",
            "Sidecars shut down",
            ["sidecar", "app", "namespace"],
        )
