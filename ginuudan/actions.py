from yaml import load

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

spec = """
- target: linkerd-proxy
  action: 
    type: portforward
    method: POST
    path: /shutdown
    port: 4191
- target: cloudsql-proxy
  action:
    type: exec
    command: kill -s INT 1
- target: secure-logs-fluentd
  action: 
    type: portforward
    method: GET
    path: /api/processes.killWorkers
    port: 24444
"""


def load_sidecar_actions():
    data = load(spec, Loader=Loader)
    return {entry["target"]: entry["action"] for entry in data}
