from os.path import exists
from enum import Enum, IntEnum
from ._TMC_2209_logger import TMC_logger, Loglevel


class Gpio(IntEnum):
    """GPIO value"""
    LOW = 0
    HIGH = 1

class GpioMode(IntEnum):
    """GPIO mode"""
    OUT = 0
    IN = 1

class GpioPUD(IntEnum):
    """Pull up Down"""
    PUD_OFF = 20
    PUD_UP = 22
    PUD_DOWN = 21


from RPi import GPIO
            
class TMC_gpio:
    """TMC_gpio class"""

    _gpios = [None] * 200

    @staticmethod
    def init(gpio_mode=None):
        """init gpio library"""
        GPIO.setwarnings(False)
        if gpio_mode is None:
            gpio_mode = GPIO.BCM
        GPIO.setmode(gpio_mode)


    @staticmethod
    def gpio_setup(pin, mode, initial = Gpio.LOW, pull_up_down = GpioPUD.PUD_OFF):
        """setup gpio pin"""

        initial = int(initial)
        pull_up_down = int(pull_up_down)
        mode = int(mode)
        if mode == GpioMode.OUT: # TODO: better way to pass different params
            GPIO.setup(pin, mode, initial=initial)
        else:
            GPIO.setup(pin, mode, pull_up_down=pull_up_down)

    @staticmethod
    def gpio_cleanup(pin):
        """cleanup gpio pin"""
        GPIO.cleanup(pin)

    @staticmethod
    def gpio_input(pin):
        """get input value of gpio pin"""
        del pin
        return 0 # TODO: implement

    @staticmethod
    def gpio_output(pin, value):
        """set output value of gpio pin"""
        GPIO.output(pin, value)

    @staticmethod
    def gpio_add_event_detect(pin, callback):
        """add event detect"""
        GPIO.add_event_detect(pin, GPIO.RISING, callback=callback,
                                bouncetime=300)

    @staticmethod
    def gpio_remove_event_detect(pin):
        """remove event dectect"""
        GPIO.remove_event_detect(pin)
