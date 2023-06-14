from .const import *

# Device models
DEVICE_MODEL_AC2729_10 = "AC2729_10"
DEVICE_MODEL_AC2889_10 = "AC2889_10"
DEVICE_MODEL_AC3259_10 = "AC3259_10"
DEFAULT_MODEL = "DEFAULT"

DEVICE_CONFIG_MODES = "device_modes"
DEVICE_CONFIG_SPEEDS = "device_speeds"
DEVICE_CONFIG_CHANGE_TO_MANUAL = "change_to_manual_mode"

MODELS = {
    DEVICE_MODEL_AC2729_10: {
        DEVICE_CONFIG_MODES: [
            MODE_ALLERGEN,
            MODE_AUTO,
            MODE_MANUAL,
            MODE_SLEEP
        ],
        DEVICE_CONFIG_SPEEDS: ALL_SPEEDS,
        DEVICE_CONFIG_CHANGE_TO_MANUAL: False,
    },
    DEVICE_MODEL_AC2889_10: {
        DEVICE_CONFIG_MODES: [
            MODE_ALLERGEN,
            MODE_AUTO,
            MODE_MANUAL,
            MODE_BACTERIA
        ],
        DEVICE_CONFIG_SPEEDS: ALL_SPEEDS,
        DEVICE_CONFIG_CHANGE_TO_MANUAL: True,
    },
    DEVICE_MODEL_AC3259_10: {
        DEVICE_CONFIG_MODES: [
            MODE_ALLERGEN,
            MODE_AUTO,
            MODE_MANUAL,
            MODE_SLEEP,
            MODE_BACTERIA,
        ],
        DEVICE_CONFIG_SPEEDS: ALL_SPEEDS,
        DEVICE_CONFIG_CHANGE_TO_MANUAL: True,
    },
    DEFAULT_MODEL: {
        DEVICE_CONFIG_MODES: ALL_MODES,
        DEVICE_CONFIG_SPEEDS: ALL_SPEEDS,
        DEVICE_CONFIG_CHANGE_TO_MANUAL: True,
    },
}