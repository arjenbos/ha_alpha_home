from homeassistant.const import Platform

DOMAIN = "alpha_innotec"

MANUFACTURER = "Alpha Innotec"

PLATFORMS = [
    Platform.SENSOR,
    Platform.CLIMATE,
]

MODULE_TYPE_FLOOR = "floor"
MODULE_TYPE_SENSOR = "sensor"

MODULE_TYPES = [
    MODULE_TYPE_FLOOR,
    MODULE_TYPE_SENSOR
]
