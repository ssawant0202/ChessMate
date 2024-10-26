"""
test file for testing multiple drivers via one UART connection
"""
import sys
import time
from src.TMC_2209_StepperDriver import *


SPEED = int(sys.argv[1])

print("---")
print("SCRIPT START")
print("---")

#-----------------------------------------------------------------------
# initiate the TMC_2209 class
# use your pins for pin_en, pin_step, pin_dir here
#-----------------------------------------------------------------------

tmc1 = TMC_2209(21, 16, 20, driver_address=0)
tmc2 = TMC_2209(26, 13, 19, driver_address=1)

#-----------------------------------------------------------------------
# set the loglevel of the libary (currently only printed)
# set whether the movement should be relative or absolute
# both optional
#-----------------------------------------------------------------------
tmc1.tmc_logger.set_loglevel(Loglevel.DEBUG)
tmc1.set_movement_abs_rel(MovementAbsRel.ABSOLUTE)

tmc2.tmc_logger.set_loglevel(Loglevel.DEBUG)
tmc2.set_movement_abs_rel(MovementAbsRel.ABSOLUTE)


for tmc in [tmc1, tmc2]:

    tmc.tmc_logger.set_loglevel(Loglevel.DEBUG)
    tmc.set_direction_reg(False)
    tmc.set_current(300)
    tmc.set_interpolation(True)
    tmc.set_spreadcycle(False)
    tmc.set_microstepping_resolution(2)
    tmc.set_internal_rsense(False)
    tmc.set_motor_enabled(True)
    tmc.set_acceleration(1000)
    tmc.set_max_speed(SPEED)
#-----------------------------------------------------------------------
# these functions read and print the current settings in the TMC register
#-----------------------------------------------------------------------

print("---")
print("IOIN tmc1")
print("---")
tmc1.read_ioin()

print("---\n---")


print("---")
print("IOIN tmc2")
print("---")
tmc2.read_ioin()

print("---\n---")


#-----------------------------------------------------------------------
# run the motors concurrently
#-----------------------------------------------------------------------

tmc1.run_to_position_steps_threaded(800, MovementAbsRel.RELATIVE)
tmc2.run_to_position_steps_threaded(1200, MovementAbsRel.RELATIVE)

tmc1.wait_for_movement_finished_threaded()
tmc1.run_to_position_steps_threaded(-400, MovementAbsRel.RELATIVE)

tmc1.wait_for_movement_finished_threaded()

#-----------------------------------------------------------------------
# deinitiate the TMC_2209 class
#-----------------------------------------------------------------------
tmc1.set_motor_enabled(False)
tmc2.set_motor_enabled(False)
del tmc1
del tmc2

print("---")
print("SCRIPT FINISHED")
print("---")
