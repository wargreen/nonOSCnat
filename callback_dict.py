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
        self.set_callback = set_callback
        self.get_callback = get_callback
        self.del_callback =s del_callback
        super().__init__(self, *args, **kwargs)

    def __getitem__(self, key):
        if self.get_callback:
            self.get_callback()
        return dict.__getitem__(self, key)

    def __setitem__(self, key, val):
        dict.__setitem__(self, key, val)
        if self.set_callback:
            self.set_callback()

    def __delitem__(self, key):
        dict.__setitem__(self, key)
        if self.del_callback:
            self.del_callback()
