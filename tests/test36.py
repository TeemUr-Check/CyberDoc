# INTENTIONALLY VULNERABLE — AI / training fixture only.
import redis

r = redis.Redis(host="127.0.0.1", port=6379)


def exec_user_script(lua: str):
    return r.eval(lua, 0)
