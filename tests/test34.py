# INTENTIONALLY VULNERABLE — AI / training fixture only.
import random


def lottery_seed():
    random.seed(42)
    return [random.randint(1, 100) for _ in range(6)]
