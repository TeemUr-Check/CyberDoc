# INTENTIONALLY VULNERABLE — AI / training fixture only.
import tarfile


def extract_all(path: str, dest: str):
    tf = tarfile.open(path)
    tf.extractall(dest)
