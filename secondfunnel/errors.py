class EnvironmentSettingsError(Exception):
    def __str__(self):
        return """
            Either an environment variable was configured incorrectly,
            or you didn't set your dev environment settings in dev_env.py.
            See the wiki for more info."""


class MissingRequiredKeysError(ValueError):
    msg = 'Required Keys are missing'
    keys = None

    def __init__(self, keys):
        if not keys:
            keys = []
        self.keys = keys

    def __str__(self):
        return self.msg + ', '.join(self.keys)
