import asyncio
from datetime import datetime

from data.fan_status import FanStatus
from controller.platform_interface import PlatformInterface

class Controller :
    def __init__(self, fan_status: FanStatus) :
        self.fan_status = fan_status
        self.fan_status.add_update_listener(self._on_updated)
        self.interface: PlatformInterface = PlatformInterface()

    def start(self) :
        asyncio.create_task(self._control_logic())

    async def _control_logic(self) :
        while True :
            temperature: float = self.interface.get_temperature()
            self.fan_status.current_temperature = temperature

            # 팬을 끄는 시간 확인
            if self._is_within_control_off_time(self.fan_status.control_off_time, self.fan_status.control_on_time) :
                self.fan_status.is_fan_on = False

            # 온도 범위 확인
            else :
                if self.interface.is_fan_on and temperature < self.fan_status.off_temperature :
                    self.fan_status.is_fan_on = False
                elif not self.interface.is_fan_on and temperature > self.fan_status.on_temperature :
                    self.fan_status.is_fan_on = True

            self.fan_status.update()
            await asyncio.sleep(1.0)

    def _on_updated(self) :
        self.interface.set_fan_on(self.fan_status.is_fan_on)

    def _is_within_control_off_time(self, control_off_time: str, control_on_time: str) -> bool:
        now = datetime.now().time()
        
        off_time = datetime.strptime(control_off_time, "%H:%M").time()
        on_time = datetime.strptime(control_on_time, "%H:%M").time()

        if off_time > on_time:
            return now >= off_time or now < on_time
        else:
            return off_time <= now < on_time
