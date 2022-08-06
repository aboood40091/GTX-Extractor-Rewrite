def divRoundUp(n, d):
    return (n + d - 1) // d


def roundUp(x, y):
    return ((x - 1) | (y - 1)) + 1
