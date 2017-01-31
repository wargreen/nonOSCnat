"""
# TODO:
"""

class CallbackDict(dict):
    """Dict with optional callbacks for set/get/del items"""
    def __init__(self, *args,
                 set_callback=None,
                 get_callback=None,
                 del_callback=None,
                 **kwargs):
        self.set_callback = set_callback if set_callback else lambda: pass
        self.get_callback = get_callback if get_callback else lambda: pass
        self.del_callback = del_callback if del_callback else lambda: pass
        super().__init__(self, *args, **kwargs)

    def __getitem__(self, key):
        self.get_callback()
        return dict.__getitem__(self, key)

    def __setitem__(self, key, val):
        dict.__setitem__(self, key, val)
        self.set_callback()

    def __delitem__(self, key):
        dict.__setitem__(self, key)
        self.del_callback()
