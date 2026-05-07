# INTENTIONALLY VULNERABLE — AI / training fixture only.
import yaml


def load_config(data: str):
    return yaml.load(data, Loader=yaml.Loader)
