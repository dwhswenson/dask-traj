#copy of varius mdtraj utils that need to loosen, to work
from __future__ import print_function, division
import warnings
import numbers
import numpy as np
import collections
from mdtraj.utils.six.moves import zip_longest
import dask.array as da

class TypeCastPerformanceWarning(RuntimeWarning):
    pass


def ensure_type(val, dtype, ndim, name, length=None, can_be_none=False,
                shape=None, warn_on_cast=True,
                add_newaxis_on_deficient_ndim=False,
                cast_da_to_np=False):
    """Typecheck the size, shape and dtype of a numpy array, with optional
    casting.
    Parameters
    ----------
    val : {np.ndaraay, None}
        The array to check
    dtype : {nd.dtype, str}
        The dtype you'd like the array to have
    ndim : int
        The number of dimensions you'd like the array to have
    name : str
        name of the array. This is used when throwing exceptions, so that
        we can describe to the user which array is messed up.
    length : int, optional
        How long should the array be?
    can_be_none : bool
        Is ``val == None`` acceptable?
    shape : tuple, optional
        What should be shape of the array be? If the provided tuple has
        Nones in it, those will be semantically interpreted as matching
        any length in that dimension. So, for example, using the shape
        spec ``(None, None, 3)`` will ensure that the last dimension is of
        length three without constraining the first two dimensions
    warn_on_cast : bool, default=True
        Raise a warning when the dtypes don't match and a cast is done.
    add_newaxis_on_deficient_ndim : bool, default=True
        Add a new axis to the beginining of the array if the number of
        dimensions is deficient by one compared to your specification. For
        instance, if you're trying to get out an array of ``ndim == 3``,
        but the user provides an array of ``shape == (10, 10)``, a new axis will
        be created with length 1 in front, so that the return value is of
        shape ``(1, 10, 10)``.
    Notes
    -----
    The returned value will always be C-contiguous.
    Returns
    -------
    typechecked_val : np.ndarray, None
        If `val=None` and `can_be_none=True`, then this will return None.
        Otherwise, it will return val (or a copy of val). If the dtype wasn't right,
        it'll be casted to the right shape. If the array was not C-contiguous, it'll
        be copied as well.
    """
    if can_be_none and val is None:
        return None

    if not isinstance(val, (np.ndarray, da.core.Array)):
        if isinstance(val, collections.Iterable):
            # If they give us an iterator, let's try...
            if isinstance(val, collections.Sequence):
                # sequences are easy. these are like lists and stuff
                val = np.array(val, dtype=dtype)
            else:
                # this is a generator...
                val = np.array(list(val), dtype=dtype)
        elif np.isscalar(val) and add_newaxis_on_deficient_ndim and ndim == 1:
            # special case: if the user is looking for a 1d array, and
            # they request newaxis upconversion, and provided a scalar
            # then we should reshape the scalar to be a 1d length-1 array
            val = np.array([val])
        else:
            raise TypeError(("%s must be numpy array. "
                " You supplied type %s" % (name, type(val))))

    if warn_on_cast and val.dtype != dtype:
        warnings.warn("Casting %s dtype=%s to %s " % (name, val.dtype, dtype),
            TypeCastPerformanceWarning)

    if not val.ndim == ndim:
        if add_newaxis_on_deficient_ndim and val.ndim + 1 == ndim:
            val = val[np.newaxis, ...]
        else:
            raise ValueError(("%s must be ndim %s. "
                "You supplied %s" % (name, ndim, val.ndim)))

    if (isinstance(val, np.ndarray)
	    or (cast_da_to_np and isinstance(val, da.core.Array))):
        val = np.ascontiguousarray(val, dtype=dtype)

    if length is not None and len(val) != length:
        raise ValueError(("%s must be length %s. "
            "You supplied %s" % (name, length, len(val))))

    if shape is not None:
        # the shape specified given by the user can look like (None, None 3)
        # which indicates that ANY length is accepted in dimension 0 or
        # dimension 1
        sentenel = object()
        error = ValueError(("%s must be shape %s. You supplied  "
                "%s" % (name, str(shape).replace('None', 'Any'), val.shape)))
        for a, b in zip_longest(val.shape, shape, fillvalue=sentenel):
            if a is sentenel or b is sentenel:
                # if the sentenel was reached, it means that the ndim didn't
                # match or something. this really shouldn't happen
                raise error
            if b is None:
                # if the user's shape spec has a None in it, it matches anything
                continue
            if a != b:
                # check for equality
                raise error
    return val
