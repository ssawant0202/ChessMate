import sys
import time
from src.TMC_2209_StepperDriver import *

SPEED = int(sys.argv[1])
THRESHOLD = int(sys.argv[2])


print("---")
print("SCRIPT START")
print("---")

#-----------------------------------------------------------------------
# initiate the TMC_2209 class
# use your pins for pin_en, pin_step, pin_dir here
#-----------------------------------------------------------------------
tmc = TMC_2209(21, 16, 20)
tmc.tmc_logger.set_loglevel(Loglevel.DEBUG)
tmc.set_movement_abs_rel(MovementAbsRel.ABSOLUTE)

#-----------------------------------------------------------------------
# these functions change settings in the TMC register
#-----------------------------------------------------------------------
tmc.set_direction_reg(False)
tmc.set_current(300)
tmc.set_interpolation(True)
tmc.set_spreadcycle(False)
tmc.set_microstepping_resolution(2)
tmc.set_internal_rsense(False)
print("---\n---")

#-----------------------------------------------------------------------
# these functions read and print the current settings in the TMC register
#-----------------------------------------------------------------------
tmc.read_ioin()
tmc.read_chopconf()
tmc.read_drv_status()
tmc.read_gconf()
print("---\n---")

#-----------------------------------------------------------------------
# set the Accerleration
#-----------------------------------------------------------------------
tmc.set_acceleration(1000)
tmc.set_motor_enabled(True)

#-----------------------------------------------------------------------
# run the motor until you stall
#-----------------------------------------------------------------------

tmc.take_me_home(speed=SPEED, threshold=THRESHOLD)
