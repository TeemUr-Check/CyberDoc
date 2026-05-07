# INTENTIONALLY VULNERABLE — AI / training fixture only.
from lxml import etree


def parse_user_xml(data: bytes):
    return etree.fromstring(data)
