# INTENTIONALLY VULNERABLE — AI / training fixture only.
import importlib


def load_plugin(name: str):
    return importlib.import_module("plugins." + name)
