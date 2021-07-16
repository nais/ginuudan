from yaml import load

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader


def load_sidecar_actions(filename):
    with open(filename) as spec:
        data = load(spec, Loader=Loader)
        actions = {entry["target"]: entry["action"] for entry in data}
