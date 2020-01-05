"""
For session store we will rely on
https://pythonhosted.org/simplekv/#
"""
from simplekv import KeyValueStore
from simplekv.fs import FilesystemStore
import random
import string
import base64
from datetime import datetime, timedelta
import json
from collections import OrderedDict
from ussd import defaults as ussd_airflow_variables

def get_random_string(length=12,
                      allowed_chars='abcdefghijklmnopqrstuvwxyz'
                                    'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'):
    """
    Return a securely generated random string.

    The default length of 12 with the a-z, A-Z, 0-9 character set returns
    a 71-bit value. log_2((26+26+10)^12) =~ 71 bits
    """
    return ''.join(random.choice(allowed_chars) for i in range(length))


date_format = '%Y-%m-%dT%H:%M:%S.%f'


class CustomJsonEncoder(json.JSONEncoder):

    def default(self, obj):
        try:
            return json.JSONEncoder.default(self, obj)
        except TypeError:
            if isinstance(obj, datetime):
                return obj.strftime(date_format)
            return obj.__class__.__name__


def datetime_parser(dct):
    dct = OrderedDict(dct)
    if dct.get(ussd_airflow_variables.session_expiry):
        dct[ussd_airflow_variables.session_expiry] = \
            datetime.strptime(dct[ussd_airflow_variables.session_expiry], date_format)
    return dct


class JSONSerializer:
    """
    Simple wrapper around json to be used in signing.dumps and
    signing.loads.
    """
    def dumps(self, obj):
        return json.dumps(obj, separators=(',', ':'), cls=CustomJsonEncoder).encode('latin-1')

    def loads(self, data):
        return json.loads(data.decode('latin-1'), object_pairs_hook=datetime_parser)


# session_key should not be case sensitive because some backends can store it
# on case insensitive file systems.
VALID_KEY_CHARS = string.ascii_lowercase + string.digits


SESSION_COOKIE_AGE = 180


class CreateError(Exception):
    """
    Used internally as a consistent exception type to catch from save (see the
    docstring for SessionBase.save() for details).
    """
    pass


class UpdateError(Exception):
    """
    Occurs if ussd tries to update a session that was deleted.
    """


class SessionStore(object):

    __not_given = object()

    def __init__(self, session_key=None,
                 kv_store: KeyValueStore = None,
                 default_session_cookie_age: int = SESSION_COOKIE_AGE):
        if kv_store is None:
            kv_store = FilesystemStore("./.session_data")
        self._session_key = session_key
        self.accessed = False
        self.modified = False
        self.serializer = JSONSerializer
        self.defaul_session_cookie_age = default_session_cookie_age
        self.kv_store = kv_store

    def __contains__(self, key):
        return key in self._session

    def __getitem__(self, key):
        return self._session[key]

    def __setitem__(self, key, value):
        self._session[key] = value
        self.modified = True

    def __delitem__(self, key):
        del self._session[key]
        self.modified = True

    def load(self):
        try:
            data = self.kv_store.get(self.session_key)
            return self.decode(data)
        except KeyError:
            return {}

    def exists(self, session_key):
        try:
            self.kv_store.get(session_key)
            return True
        except KeyError:
            return False

    def get(self, key, default=None):
        return self._session.get(key, default)

    def pop(self, key, default=__not_given):
        self.modified = self.modified or key in self._session
        args = () if default is self.__not_given else (default,)
        return self._session.pop(key, *args)

    def setdefault(self, key, value):
        if key in self._session:
            return self._session[key]
        else:
            self.modified = True
            self._session[key] = value
            return value

    def delete(self, session_key=None):
        if session_key is None:
            if self.session_key is None:
                return
            session_key = self.session_key
        self.kv_store.delete(session_key)

    def create(self):
        self._session_key = self._get_new_session_key()
        self.save(must_create=True)

    def save(self, must_create=False):
        if self.session_key is None:
            return self.create()
        data = self._get_session(no_load=must_create)

        self.set_expiry(self.get_expiry_date())
        self.kv_store.put(self.session_key, self.encode(data))

    def update(self, dict_):
        self._session.update(dict_)
        self.modified = True

    def has_key(self, key):
        return key in self._session

    def keys(self):
        return self._session.keys()

    def values(self):
        return self._session.values()

    def items(self):
        return self._session.items()

    def key_pair(self):
        return self._session

    def clear(self):
        # To avoid unnecessary persistent storage accesses, we set up the
        # internals directly (loading data wastes time, since we are going to
        # set it to an empty dict anyway).
        self._session_cache = {}
        self.accessed = True
        self.modified = True

    def encode(self, session_dict):
        """Return the given session dictionary serialized and encoded as a string."""
        serialized = self.serializer().dumps(session_dict)
        return base64.b64encode(serialized)

    def decode(self, session_data):
        encoded_data = base64.b64decode(session_data)
        return self.serializer().loads(encoded_data)

    def _get_new_session_key(self):
        "Return session key that isn't being used."
        while True:
            session_key = get_random_string(32, VALID_KEY_CHARS)
            if not self.exists(session_key):
                return session_key

    def _get_session(self, no_load=False):
        """
        Lazily load session from storage (unless "no_load" is True, when only
        an empty dict is stored) and store it in the current instance.
        """
        self.accessed = True
        try:
            return self._session_cache
        except AttributeError:
            if self.session_key is None or no_load:
                self._session_cache = {}
            else:
                self._session_cache = self.load()
        return self._session_cache

    @staticmethod
    def _validate_session_key(key):
        """
        Key must be truthy and at least 8 characters long. 8 characters is an
        arbitrary lower bound for some minimal key security.
        """
        return key and len(key) >= 8

    def _set_session_key(self, value):
        """
        Validate session key on assignment. Invalid values will set to None.
        """
        if self._validate_session_key(value):
            self.__session_key = value
        else:
            self.__session_key = None

    def _get_session_key(self):
        return self.__session_key

    _session_key = property(_get_session_key, _set_session_key)
    session_key = property(_get_session_key)
    _session = property(_get_session)

    def get_expiry_age(self, **kwargs):
        """Get the number of seconds until the session expires.

        Optionally, this function accepts `modification` and `expiry` keyword
        arguments specifying the modification and expiry of the session.
        """
        try:
            modification = kwargs['modification']
        except KeyError:
            modification = datetime.now()
        # Make the difference between "expiry=None passed in kwargs" and
        # "expiry not passed in kwargs", in order to guarantee not to trigger
        # self.load() when expiry is provided.
        try:
            expiry = kwargs['expiry']
        except KeyError:
            expiry = self.get('_session_expiry')

        if not expiry:   # Checks both None and 0 cases
            return self.defaul_session_cookie_age
        if not isinstance(expiry, datetime):
            return expiry
        delta = expiry - modification
        return delta.days * 86400 + delta.seconds

    def get_expiry_date(self, **kwargs):
        """Get session the expiry date (as a datetime object).

        Optionally, this function accepts `modification` and `expiry` keyword
        arguments specifying the modification and expiry of the session.
        """
        try:
            modification = kwargs['modification']
        except KeyError:
            modification = datetime.now()
        # Same comment as in get_expiry_age
        try:
            expiry = kwargs['expiry']
        except KeyError:
            expiry = self.get(ussd_airflow_variables.session_expiry)

        if isinstance(expiry, datetime):
            return expiry
        expiry = expiry or SESSION_COOKIE_AGE   # Checks both None and 0 cases
        return modification + timedelta(seconds=expiry)

    def set_expiry(self, value):
        """
        Set a custom expiration for the session. ``value`` can be an integer,
        a Python ``datetime`` or ``timedelta`` object or ``None``.

        If ``value`` is an integer, the session will expire after that many
        seconds of inactivity. If set to ``0`` then the session will expire on
        browser close.

        If ``value`` is a ``datetime`` or ``timedelta`` object, the session
        will expire at that specific future time.

        If ``value`` is ``None``, the session uses the global session expiry
        policy.
        """
        if value is None:
            # Remove any custom expiration for this session.
            try:
                del self['_session_expiry']
            except KeyError:
                pass
            return
        if isinstance(value, timedelta):
            value = datetime.now() + value
        self[ussd_airflow_variables.session_expiry] = value

    def flush(self):
        """
        Remove the current session data from the database and regenerate the
        key.
        """
        self.clear()
        self.delete()
        self._session_key = None

    def cycle_key(self):
        """
        Create a new session key, while retaining the current session data.
        """
        data = self._session
        key = self.session_key
        self.create()
        self._session_cache = data
        if key:
            self.delete(key)

    def cycle_data(self):
        """
        Creates a new session key saves the current data to that session key clears data of
        the current session key
        :return:
        """
        original_key = self.session_key
        # will set a new key and save data to that key
        self.create()
        new_key = self.session_key

        self._session_key = original_key
        self.clear()
        self.save()

        return new_key
