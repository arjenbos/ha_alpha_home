class Valve:
    def __init__(self, identifier: str, name: str, instance: str, device_id: str, device_name: str, status: bool, used: bool):
        self.identifier = identifier
        self.name = name
        self.instance = instance
        self.device_id = device_id
        self.device_name = device_name
        self.status = status
        self.used = used
