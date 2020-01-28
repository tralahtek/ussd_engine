from ..journey_store import JourneyStore
from collections import OrderedDict

store = OrderedDict()


class DummyStore(JourneyStore):
    """
    This store should not be used in production only meant to test the interface
    """
    
    def __init__(self, user="default"):
        self.user = user
        if not store.get(self.user):
            store[user] = {}
        self.store = store[user]
            
    def _get(self, name, version, screen_name, **kwargs):
        if version == 'edit_mode':
            return self.store.get('edit_mode', {}).get(name)
        if self.store.get(name):
            if version is None:  # get the latest journey created
                journey = self.store[name][next(reversed(self.store[name]))]
            else:
                journey = self.store[name].get(version)
            if screen_name is not None:
                return journey.get(screen_name)
            return journey
        return None

    def _get_all_journey_version(self, name):
        return self.store.get(name, {})

    def _save(self, name, journey, version):
        if version == self.edit_mode_version:
            self.store['edit_mode'] = {name: journey}
        else:
            if self.store.get(name):
                self.store[name][version] = journey
            else:
                self.store[name] = OrderedDict({version: journey})
        return journey

    def _delete(self, name, version=None):
        if self.store.get(name):
            if self.store[name].get(version):
                del self.store[name][version]
            else:
                del self.store[name]
    
    def _all(self):
        return self.store
    
    def flush(self):
        pass

