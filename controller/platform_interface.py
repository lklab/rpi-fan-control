class PlatformInterface:
    FAN_PIN = 21

    def __init__(self):
        self.is_rasp = self._check_raspberry_pi()
        print(f'is_rasp: {self.is_rasp}')

        self.is_fan_on: bool = False

        if self.is_rasp:
            try:
                import RPi.GPIO as GPIO
                self.GPIO = GPIO

                self.GPIO.setmode(self.GPIO.BCM)
                self.GPIO.setup(self.FAN_PIN, self.GPIO.OUT)
                self.set_fan_on(False, force=True)
            except RuntimeError as e:
                print(f"GPIO 초기화 실패: {e}")
                self.is_rasp = False

    def _check_raspberry_pi(self) -> bool:
        """라즈베리 파이에서 실행 중인지 확인"""
        try:
            with open("/proc/cpuinfo", "r") as f:
                return "raspberry" in f.read().lower()
        except FileNotFoundError:
            return False

    def set_fan_on(self, on: bool, force: bool = False):
        """팬을 켜거나 끄는 함수"""
        if self.is_fan_on != on or force :
            self.is_fan_on = on
            if self.is_rasp:
                self.GPIO.output(self.FAN_PIN, not on)

    def get_temperature(self) -> float:
        """CPU 온도를 읽는 함수"""
        if self.is_rasp:
            try:
                with open("/sys/class/thermal/thermal_zone0/temp", "r") as file:
                    return float(file.read()) / 1000.0
            except Exception as e:
                print(f"온도 읽기 실패: {e}")
                return -1.0
        else:
            return 30.0
