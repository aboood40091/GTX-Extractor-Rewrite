from .._cython import is_available as _is_cython_available


if _is_cython_available:
    from .format_utils_cy import *

else:
    from .format_utils import *
