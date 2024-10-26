#pylint: disable=invalid-name
#pylint: disable=no-member
#pylint: disable=too-many-arguments
#pylint: disable=too-many-public-methods
#pylint: disable=too-many-branches
#pylint: disable=too-many-instance-attributes
#pylint: disable=import-outside-toplevel
#pylint: disable=bare-except
"""TMC_2209 stepper driver module

this module has two different functions:
1. change setting in the TMC-driver via UART
2. move the motor via STEP/DIR pins
"""

import time
import statistics
import logging
from ._TMC_2209_GPIO_board import TMC_gpio, Gpio, GpioMode, GpioPUD
from ._TMC_2209_uart import TMC_UART as tmc_uart
from ._TMC_2209_logger import TMC_logger, Loglevel
from ._TMC_2209_move import MovementAbsRel, MovementPhase, StopMode, Direction, MAX_STEPS_ALLOWED
from . import _TMC_2209_math as tmc_math



class TMC_2209:
    """TMC_2209

    this class has two different functions:
    1. change setting in the TMC-driver via UART
    2. move the motor via STEP/DIR pins
    """

    from ._TMC_2209_comm import (
        read_drv_status, read_gconf, read_gstat, clear_gstat, read_ioin, read_chopconf,
        get_direction_reg, set_direction_reg, get_iscale_analog, set_iscale_analog,get_vsense,
        set_vsense, get_internal_rsense, set_internal_rsense, set_irun_ihold, set_pdn_disable,
        set_current, get_spreadcycle, set_spreadcycle, get_interpolation, set_interpolation,
        read_microstepping_resolution, get_microstepping_resolution, set_microstepping_resolution,
        set_mstep_resolution_reg_select, get_interface_transmission_counter, get_tstep, set_vactual,
        get_stallguard_result, set_stallguard_threshold, set_coolstep_threshold,
        get_microstep_counter, get_microstep_counter_in_steps, set_toff
    )

    from ._TMC_2209_move import (
        set_movement_abs_rel, get_current_position, set_current_position, set_max_speed,
        set_max_speed_fullstep, get_max_speed, set_acceleration, set_acceleration_fullstep,
        get_acceleration, stop, get_movement_phase, run_to_position_steps,
        run_to_position_revolutions, run_to_position_steps_threaded,
        run_to_position_revolutions_threaded, wait_for_movement_finished_threaded, run,
        distance_to_go, compute_new_speed, run_speed, make_a_step
    )

    from ._TMC_2209_test import (
        test_dir_step_en, test_step, test_uart, test_stallguard_threshold
    )

    tmc_uart = None
    tmc_logger = None
    _pin_step = -1
    _pin_dir = -1
    _pin_en = -1
    _pin_stallguard = -1

    _direction = True

    _stop = StopMode.NO
    _starttime = 0
    _sg_callback = None

    _msres = -1
    _steps_per_rev = 0
    _fullsteps_per_rev = 200

    _current_pos = 0                 # current position of stepper in steps
    _target_pos = 0                  # the target position in steps
    _speed = 0.0                    # the current speed in steps per second
    _max_speed = 1.0                 # the maximum speed in steps per second
    _max_speed_homing = 200           # the maximum speed in steps per second for homing
    _acceleration = 1.0             # the acceleration in steps per second per second
    _acceleration_homing = 10000     # the acceleration in steps per second per second for homing
    _sqrt_twoa = 1.0                # Precomputed sqrt(2*_acceleration)
    _step_interval = 0               # the current interval between two steps
    _min_pulse_width = 1              # minimum allowed pulse with in microseconds
    _last_step_time = 0               # The last step time in microseconds
    _n = 0                          # step counter
    _c0 = 0                         # Initial step size in microseconds
    _cn = 0                         # Last step size in microseconds
    _cmin = 0                       # Min step size in microseconds based on maxSpeed
    _sg_threshold = 100             # threshold for stallguard
    _movement_abs_rel = MovementAbsRel.ABSOLUTE
    _movement_phase = MovementPhase.STANDSTILL

    _movement_thread = None

    _deinit_finished = False



    def __init__(self, pin_en, pin_step=-1, pin_dir=-1, baudrate=115200, serialport="/dev/serial0",
                 driver_address=0, gpio_mode=None, loglevel=None, logprefix=None,
                 log_handlers: list = None, log_formatter : logging.Formatter = None,
                 skip_uart_init: bool = False):
        """constructor

        Args:
            pin_en (int): EN pin number
            pin_step (int, optional): STEP pin number. Defaults to -1.
            pin_dir (int, optional): DIR pin number. Defaults to -1.
            baudrate (int, optional): baudrate. Defaults to 115200.
            serialport (str, optional): serialport path. Defaults to "/dev/serial0".
            driver_address (int, optional): driver address [0-3]. Defaults to 0.
            gpio_mode (enum, optional): gpio mode. Defaults to None.
            loglevel (enum, optional): loglevel. Defaults to None.
            logprefix (str, optional): log prefix (name of the logger).
                Defaults to None (standard TMC prefix).
            log_handlers (list, optional): list of logging handlers.
                Defaults to None (log to console).
            log_formatter (logging.Formatter, optional): formatter for the log messages.
                Defaults to None (messages are logged in the format
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s').
            skip_uart_init (bool, optional): skip UART init. Defaults to False.
        """
        if logprefix is None:
            logprefix = f"TMC2209 {driver_address}"
        self.tmc_logger = TMC_logger(loglevel, logprefix, log_handlers, log_formatter)
        self.tmc_uart = tmc_uart(self.tmc_logger, serialport, baudrate, driver_address)


        self.tmc_logger.log("Init", Loglevel.INFO)
        TMC_gpio.init(gpio_mode)

        self.tmc_logger.log(f"EN Pin: {pin_en}", Loglevel.DEBUG)
        self._pin_en = pin_en
        TMC_gpio.gpio_setup(self._pin_en, GpioMode.OUT, initial=Gpio.HIGH)

        self.tmc_logger.log(f"STEP Pin: {pin_step}", Loglevel.DEBUG)
        if pin_step != -1:
            self._pin_step = pin_step
            TMC_gpio.gpio_setup(self._pin_step, GpioMode.OUT, initial=Gpio.LOW)

        self.tmc_logger.log(f"DIR Pin: {pin_dir}", Loglevel.DEBUG)
        if pin_dir != -1:
            self._pin_dir = pin_dir
            TMC_gpio.gpio_setup(self._pin_dir, GpioMode.OUT, initial=self._direction)

        self.tmc_logger.log("GPIO Init finished", Loglevel.INFO)

        if not skip_uart_init:
            self.read_steps_per_rev()
            self.clear_gstat()

        self.tmc_uart.flush_serial_buffer()
        self.tmc_logger.log("Init finished", Loglevel.INFO)

        self.set_max_speed_fullstep(100)
        self.set_acceleration_fullstep(100)



    def __del__(self):
        """destructor"""
        if self._deinit_finished is False:
            self.tmc_logger.log("Deinit", Loglevel.INFO)

            self.set_motor_enabled(False)

            self.tmc_logger.log("GPIO cleanup", Loglevel.INFO)
            if self._pin_step != -1:
                TMC_gpio.gpio_cleanup(self._pin_step)
            if self._pin_dir != -1:
                TMC_gpio.gpio_cleanup(self._pin_dir)
            if self._pin_en != -1:
                TMC_gpio.gpio_cleanup(self._pin_en)
            if self._pin_stallguard != -1:
                TMC_gpio.gpio_remove_event_detect(self._pin_stallguard)
                TMC_gpio.gpio_cleanup(self._pin_stallguard)

            self.tmc_logger.log("Deinit finished", Loglevel.INFO)
            self._deinit_finished= True
        else:
            self.tmc_logger.log("Deinit already finished", Loglevel.INFO)
        del self.tmc_uart
        del self.tmc_logger



    def set_deinitialize_true(self):
        """set deinitialize to true"""
        self._deinit_finished = True


    def set_motor_enabled(self, en):
        """enables or disables the motor current output

        Args:
            en (bool): whether the motor current output should be enabled
        """
        TMC_gpio.gpio_output(self._pin_en, not en)
        self.tmc_logger.log(f"Motor output active: {en}", Loglevel.INFO)


    def reverse_direction_pin(self):
        """reverses the motor shaft direction"""
        self._direction = not self._direction
        TMC_gpio.gpio_output(self._pin_dir, self._direction)


    def set_direction_pin(self, direction):
        """sets the motor shaft direction to the given value: 0 = CCW; 1 = CW

        Args:
            direction (bool): motor shaft direction: False = CCW; True = CW
        """
        self._direction = direction
        TMC_gpio.gpio_output(self._pin_dir, direction)


    def read_steps_per_rev(self):
        """returns how many steps are needed for one revolution.
        this reads the value from the self driver.

        Returns:
            int: Steps per revolution
        """
        self._steps_per_rev = self._fullsteps_per_rev*self.read_microstepping_resolution()
        return self._steps_per_rev


    def get_steps_per_rev(self):
        """returns how many steps are needed for one revolution.
        this gets the cached value from the library.

        Returns:
            int: Steps per revolution
        """
        return self._steps_per_rev


    def set_stallguard_callback(self, pin_stallguard, threshold, callback,
                                min_speed = 100):
        """set a function to call back, when the driver detects a stall
        via stallguard
        high value on the diag pin can also mean a driver error

        Args:
            pin_stallguard (int): pin needs to be connected to DIAG
            threshold (int): value for SGTHRS
            callback (func): will be called on StallGuard trigger
            min_speed (int): min speed [steps/s] for StallGuard (Default value = 100)
        """
        self.tmc_logger.log(f"setup stallguard callback on GPIO {pin_stallguard}",
                            Loglevel.INFO)
        self.tmc_logger.log(f"""StallGuard Threshold: {threshold}
                            minimum Speed: {min_speed}""", Loglevel.INFO)

        self.set_stallguard_threshold(threshold)
        self.set_coolstep_threshold(tmc_math.steps_to_tstep(
            min_speed, self.get_microstepping_resolution()))
        self._sg_callback = callback
        self._pin_stallguard = pin_stallguard

        TMC_gpio.gpio_setup(self._pin_stallguard, GpioMode.IN, pull_up_down=GpioPUD.PUD_DOWN)
        # first remove existing events
        TMC_gpio.gpio_remove_event_detect(self._pin_stallguard)
        TMC_gpio.gpio_add_event_detect(self._pin_stallguard, self.stallguard_callback)



    def stallguard_callback(self, gpio_pin):
        """the callback function for StallGuard.
        only checks whether the duration of the current movement is longer than
        _sg_delay and then calls the actual callback

        Args:
            gpio_pin (int): pin number of the interrupt pin
        """
        del gpio_pin
        if self._sg_callback is None:
            self.tmc_logger.log("StallGuard callback is None", Loglevel.DEBUG)
            return
        self._sg_callback()

    def take_me_home(self, threshold, direction: int = Direction.CW):

        self.tmc_logger.log(f"Testing homing with threshold = {threshold}", Loglevel.INFO)
        self.set_spreadcycle(0)
        if direction == Direction.CCW:
            steps = MAX_STEPS_ALLOWED * (-1)
        elif direction == Direction.CW:
            steps = MAX_STEPS_ALLOWED
        self.run_to_position_steps_threaded(steps, MovementAbsRel.RELATIVE)
        #print("Position: ", self.get_current_position())
        while self.get_movement_phase() != MovementPhase.STANDSTILL:
            stallguard_result = self.get_stallguard_result()

            if (self.get_movement_phase() == MovementPhase.MAXSPEED and
                stallguard_result < threshold):
                #print("Position: ", self.get_current_position())
                self.stop()
                break

        self.wait_for_movement_finished_threaded()
