# INTENTIONALLY VULNERABLE — AI / training fixture only.
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad


def encrypt_block(key: bytes, plaintext: bytes) -> bytes:
    cipher = AES.new(key, AES.MODE_ECB)
    return cipher.encrypt(pad(plaintext, AES.block_size))
