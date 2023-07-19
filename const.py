from homeassistant.const import Platform

DOMAIN = "alpha"

PLATFORMS = [
    Platform.CLIMATE,
]

MODULE_TYPE_FLOOR = "floor"
MODULE_TYPE_SENSOR = "sensor"

MODULE_TYPES = [
    MODULE_TYPE_FLOOR,
    MODULE_TYPE_SENSOR
]