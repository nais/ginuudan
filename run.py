import subprocess


def kopf():
    cmd = ["kopf", "run", "-v", "--log-format=json", "ginuudan/__main__.py"]
    subprocess.run(cmd)


def black():
    cmd = ["black", "."]
    subprocess.run(cmd)
