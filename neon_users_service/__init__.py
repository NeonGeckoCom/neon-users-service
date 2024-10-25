from os import environ
from os.path import join, dirname

environ.setdefault('OVOS_CONFIG_FILENAME', "diana.yaml")
environ.setdefault('OVOS_CONFIG_BASE_FOLDER', "neon")
environ.setdefault('OVOS_DEFAULT_CONFIG', join(dirname(__file__), "default_config.yaml"))
