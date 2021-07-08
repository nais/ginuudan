from kubernetes import config
from kubernetes.client import Configuration
from kubernetes.client.api import core_v1_api


def init_corev1():
    config.load_kube_config()
    c = Configuration.get_default_copy()
    c.assert_hostname = False
    Configuration.set_default(c)
    return core_v1_api.CoreV1Api()
