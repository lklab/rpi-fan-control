from typing import Callable
import json
import os

SETTING_FILE_PATH = 'config/settings.json'

class FanStatus :
    def __init__(self) :
        self.is_fan_on: bool = False
        self.current_temperature: float = 25.0
        self.update_listeners: list[Callable[[], None]] = []

        if os.path.exists(SETTING_FILE_PATH):
            with open(SETTING_FILE_PATH, encoding='utf-8') as f :
                json_data = json.load(f)

            self.off_temperature: float = json_data['off_temp']
            self.on_temperature: float = json_data['on_temp']
            self.control_off_time: str = json_data['control_off_time']
            self.control_on_time: str = json_data['control_on_time']
        else:
            self.off_temperature: float = 38.0
            self.on_temperature: float = 45.0
            self.control_off_time: str = '23:30'
            self.control_on_time: str = '08:00'
            self.update()

    def add_update_listener(self, listener: Callable[[], None]) :
        self.update_listeners.append(listener)

    def remove_update_listener(self, listener: Callable[[], None]) :
        try :
            self.update_listeners.remove(listener)
        except :
            pass

    def update(self) :
        json_data = {}
        json_data['off_temp'] = self.off_temperature
        json_data['on_temp'] = self.on_temperature
        json_data['control_off_time'] = self.control_off_time
        json_data['control_on_time'] = self.control_on_time

        with open(SETTING_FILE_PATH, 'w', encoding='utf-8') as file :
            json.dump(json_data, file, indent=4, ensure_ascii=False)

        for listener in self.update_listeners :
            listener()
