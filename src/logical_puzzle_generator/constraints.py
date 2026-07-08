from typing import Callable

def left_of(a: str, b: str) -> Callable[[dict[str,int]], bool]:
    return lambda s: s[a] < s[b]

def right_of(a: str, b: str):
    return lambda s: s[a] > s[b]

def adjacent(a: str, b: str):
    return lambda s: abs(s[a]-s[b]) == 1

def fixed_position(a: str, pos: int):
    return lambda s: s[a] == pos
