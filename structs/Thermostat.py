class Thermostat:
    def __init__(self, identifier: str, name: str, current_temperature: float = None,
                 minimum_temperature: float = None, maximum_temperature: float = None,
                 desired_temperature: float = None, battery_percentage: int = None,
                 cooling: bool = None,
                 cooling_enabled: bool = False
                 ):
        self.identifier = identifier
        self.name = name
        self.current_temperature = current_temperature
        self.minimum_temperature = minimum_temperature
        self.maximum_temperature = maximum_temperature
        self.battery_percentage = battery_percentage
        self.desired_temperature = desired_temperature
        self.cooling = cooling
        self.cooling_enabled = cooling_enabled
