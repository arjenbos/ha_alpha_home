from homeassistant.const import Platform

DOMAIN = "alpha_innotec"

MANUFACTURER = "Alpha Innotec"

PLATFORMS = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.CLIMATE,
]

MODULE_TYPE_FLOOR = "floor"
MODULE_TYPE_SENSOR = "sensor"
MODULE_TYPE_SENSE_CONTROL = "sense_control"

MODULE_TYPES = [
    MODULE_TYPE_FLOOR,
    MODULE_TYPE_SENSOR,
    MODULE_TYPE_SENSE_CONTROL
]
