try:
    import pyximport
    pyximport.install()

    import cython_available

except Exception:
    is_available = False

else:
    is_available = True
