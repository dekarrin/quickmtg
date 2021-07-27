import os.path
import pickle
import logging
from typing import Any, Callable, Dict, Optional, Tuple, TypeVar, Union

T = TypeVar('T')

_log = logging.getLogger(__name__)
_log.setLevel(logging.DEBUG)


class PathCache:
    def __init__(self, existing_store: Optional[Dict]=None):
        self._store = dict()
        if existing_store is not None:
            self._store = dict(existing_store)

    def clear(self, path: str):
        """
        Clear all entries at the given path recursively.
        """
        path = path.lstrip('/')

        if path == '':
            self._store = dict()

        comps = list(path.split('/'))
        
        # if any part of the path does not exist, already done
        search = self._store
        for c in comps[:-1]:
            if c not in search:
                return
            search = search[c]

        # check for the actual comp to delete
        if comps[-1] in search:
            del search[comps[-1]]

    def reset(self):
        """Remove all entries and reset the cache."""
        self._store = dict()

    def set(self, path: str, value: Any):
        """Set the value at the given path. If it doesn't yet exist, it is created."""
        path = path.lstrip('/')

        if path == '':
            raise TypeError("Empty or root as path is invalid")

        comps = list(path.split('/'))

        cur = self._store
        navpath = ''
        for c in comps[:-1]:
            navpath += '/' + c
            if c not in cur:
                cur[c] = dict()
            if not isinstance(cur[c], dict):
                raise TypeError("Invalid path: object at {!r} is not a dict".format(navpath))
            cur = cur[c]
        
        # now add the actual item
        cur[comps[-1]] = value

    def get(self, path: str, conv: Callable[[Any], Any]=None) -> Tuple[Any, bool]:
        """Get the item at the given path. If it doesn't exist, (None, False) is
        returned; otherwise (value, True) is returned where value is the value
        stored at that path.
        
        :param path: Path to the item to get.
        :param conv: If set, when an item is found, this function is called on
        it before it is returned. This function will not be called if the path
        refers to an object that doesn't yet exist in the store.
        """
        path = path.lstrip('/')

        if path == '':
            raise TypeError("Empty or root as path is invalid")

        comps = list(path.split('/'))

        cur = self._store
        navpath = ''
        for c in comps[:-1]:
            navpath += '/' + c
            if c not in cur:
                return (None, False)
            if not isinstance(cur[c], dict):
                raise TypeError("Invalid path: object at {!r} is not a dict".format(navpath))
            cur = cur[c]

        if comps[-1] not in cur:
            return (None, False)

        data = cur[comps[-1]]
        if conv is not None:
            data = conv(data)
        return (data, True)

    @property
    def store(self) -> dict:
        """Return the store as a dict, for pickling."""
        return self._store

    
class FileCache(PathCache):
    def __init__(self, root_dir: str, existing_store: Optional[Dict]=None):
        super().__init__(existing_store)
        self._root = root_dir
        
        try:
            os.mkdir(root_dir)
        except FileExistsError:
            pass
            # It's fine if it already exists
        
        if not os.path.isdir(root_dir):
            raise ValueError("{!r} does not exist for local file cache".format(root_dir))

    def reset(self):
        """Delete all local files to reset the cache."""
        self.clear('/')

    def clear(self, path: str):
        """
        Clear all entries at the given path recursively.
        """
        path = path.strip('/')
        if path == '':
            start = self._store
        else:
            comps = list(path.split('/'))
            cur = self._store
            for p in comps:
                if p not in cur:
                    # we are done, it's already clear
                    super().clear(path)
                    return
                cur = cur[p]
            start = cur

        _recurse(lambda path, _: os.unlink(path), start, self._root)
        super().clear(path)

    def set(self, path: str, value: bytes):
        """Set the file at the given path. If it doesn't yet exist, it is
        created, as is any parent directories"""
        joined_path = '/'.join([self._root.rstrip('/'), path.lstrip('/')])
        full_path = os.path.abspath(joined_path)
        size = len(value)
        super().set(path, {'filepath': full_path, 'size': size})

        norm_path = path.strip('/')
        if norm_path == '':
            # it won't be, that's not allowed by super().set(), but double check anyways
            raise ValueError('Path cannot be root or empty')
        
        comps = norm_path.split('/')
        partial_path = self._root
        try:
            for c in comps[:-1]:
                partial_path = os.path.join(partial_path, c)
                try:
                    os.mkdir(partial_path)
                except FileExistsError:
                    pass
                    # this is fine, just dont create the dir
            
            # okay, now actually create the file, since parent dirs have been
            # made
            with open(full_path, 'wb') as fp:
                fp.write(value)
        except:
            super().clear(path)
            raise
    
    def get(self, path: str, conv: Callable[[bytes], T]=None) -> Tuple[Tuple[Union[bytes, T], Any], bool]:
        """Get the file at the given path. If it doesn't exist, (None, False) is
        returned; otherwise ((filebytes, metadata), True) is returned where
        value is the value stored at that path.

        :param path: Path to the item to get.
        :param conv: If set, when an item is found, this function is called on
        its bytes and the resulting object is returned. This function will not
        be called if the path refers to an object that doesn't yet exist in the
        store.
        """
        meta, exists = super().get(path)
        if not exists:
            return None, False
        
        filepath = meta['filepath']
        size = meta['size']

        try:
            with open(filepath, 'rb') as fp:
                data = fp.read(size)
        except FileNotFoundError:
            # remove from cache; file has been tampered with and there is no
            # point in keeping it in records
            super().clear(path)
            return None, False

        if conv is not None:
            data = conv(data)
        
        return (data, meta), True


class AutoSaveStore:
    """
    Store that automatically saves whenever it is updated. Data points are
    stored in path-like hierarchy as is the case with PathCache.
    """

    def __init__(self, path: str):
        """
        Create new store.
        
        :param path: The path to the file to store the cache in. Will be created
        if it doesn't already exist on the first update.
        """
        self.path = path
        self._cache = PathCache()
        self._batch = False

        try:
            with open(path, 'rb') as fp:
                data = pickle.load(fp)
        except FileNotFoundError:
            pass
        else:
            try:
                self._cache = PathCache(existing_store=data)
            except:
                _log.exception("Problem reading store persist file")
                _log.warn("Couldn't read persist file; skipping loading of it")

    def save(self):
        """
        Force an immediate save to disk without performing an update.
        """
        try:
            with open(self.path, 'wb') as fp:
                pickle.dump(self._cache.store, fp)
        except:
            _log.exception("Problem saving store persist file")
            _log.warn("Couldn't save store persist file")

    def clear(self, path: str):
        """
        Clear all entries at the given path recursively.
        """
        self._cache.clear(path)
        self.save()

    def batch(self):
        """
        Setup a batch process. Will not commit changes until commit() is called.
        """
        self._batch = True

    def commit(self):
        """
        Commit the batched changes. Also ends the batch, so further updates will
        resume normal behavior of immediately saving after.

        If not in a batch, has no effect.
        """
        if not self._batch:
            return
        self.save()
        self._batch = False

    def reset(self):
        """Remove all entries and reset the cache."""
        self._cache.reset()
        if not self._batch:
            self.save()

    def set(self, path: str, value: Any):
        """Set the value at the given path. If it doesn't yet exist, it is created."""
        self._cache.set(path, value)
        if not self._batch:
            self.save()

    def get(self, path: str, conv: Callable[[Any], Any]=None) -> Tuple[Any, bool]:
        """Get the item at the given path. If it doesn't exist, (None, False) is
        returned; otherwise (value, True) is returned where value is the value
        stored at that path.

        :param path: Path to the item to get.
        :param conv: If set, when an item is found, this function is called on
        it before it is returned. This function will not be called if the path
        refers to an object that doesn't yet exist in the store.
        """
        return self._cache.get(path, conv)


def _recurse(leaf_fn: Callable[[str, Any], Any], obj: Union[str, Dict[str, Any]], cur_path: str):
    """Recurse on file-like paths, dont really care about the values"""
    if isinstance(obj, dict):
        for k in obj:
            full_path = os.path.join(cur_path, k)
            _recurse(leaf_fn, obj[k], full_path)
    else:
        leaf_fn(cur_path, obj)
    
