class EnvironmentSettingsError(Exception):
    def __str__(self):
        return """
            Either an environment variable was configured incorrectly,
            or you didn't set your dev environment settings in dev_env.py.
            See the wiki for more info."""
