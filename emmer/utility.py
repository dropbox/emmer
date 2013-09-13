def lock(function):
    """A decorator to use to lock an instance of a class. The instance must
    have a `lock` instance variable already initialized.
    """
    def decorator(self, *args):
        self.lock.acquire()
        natural_return_value = function(self, *args)
        self.lock.release()
        return natural_return_value

    return decorator
