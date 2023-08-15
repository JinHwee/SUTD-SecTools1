"""
@author: Mohamed Meeran
"""
Banner = r"""
      o__ __o       o__ __o           o         
     /v     v\     /v     v\         <|>        
    />       <\   />       <\        / \        
  o/             _\o____           o/   \o      
 <|                   \_\__o__    <|__ __|>     
  \\                        \     /       \     
    \         /   \         /   o/         \o   
     o       o     o       o   /v           v\  
     <\__ __/>     <\__ __/>  />             <\ 
"""
print(Banner)
import random
random.seed(42)     # allow for a stream of pseudo-random numbers for debugging purposes across team members
import pandas as pd
import scipy.stats as stats
import matplotlib.pyplot as plt
import os
from timeit import default_timer as timer
from simulator_helper import events_per_second

# Initialized Values
ATTACK_TYPES = ["NONE", "BIAS", "SURGE", "RANDOM"]
DEBUG = True # Variable to print simulation values
SHOW_PLOTS = True # Variable to show plots during debug
SAVE_PLOTS = True # Variable to save plots during run
LOW_WATER_LEVEL = 500
HIGH_WATER_LEVEL = 800
INITIAL_WATER_LEVEL = random.randint(500,800) # To make both actuators run at the start
INFLOW_PUMP_AND_VALVE = 1.11857/events_per_second() # Flow of water inside the tank when valve is open and pump is running
INFLOW_NOT_PUMP_AND_VALVE = 28.5234/events_per_second() # Flow of water inside the tank when valve is open and pump is off
INFLOW__PUMP_AND_NOT_VALVE = -27.40/events_per_second() # Flow of water outside the tank when valve is closed and pump is running
RUNS = 10 # Number of simulation runs
SIMULATION_TIME = 500 # Number of simulation step per each run

# Creating folder to save plots and results
def init_folders():
    if "output" not in os.listdir():
        print("Creating output folder...")
        os.mkdir("output")
        for at in ATTACK_TYPES:
            os.mkdir("output/ATTACK_TYPE_%s" % (at))
            os.mkdir("output/ATTACK_TYPE_%s/MULTIPOINT" % (at))
    else:
        print("Output folder already exists. Skipping creation of output folder.")

# Get status of Actuators
def get_p_and_v(water_level):
    if water_level <= LOW_WATER_LEVEL:
        pump = False
        valve = True
    elif water_level >= HIGH_WATER_LEVEL:
        pump = True
        valve = False
    elif water_level > LOW_WATER_LEVEL and water_level < HIGH_WATER_LEVEL:
        pump = True
        valve = True  # T301 is always in need of water, pump should always be Open where feasible
    return pump, valve

# Get status of water level with respect to status of actuators
def get_rate(pump, valve):
    if pump and valve:
        return INFLOW_PUMP_AND_VALVE
    elif not pump and valve:
        return INFLOW_NOT_PUMP_AND_VALVE
    elif pump and not valve:
        return INFLOW__PUMP_AND_NOT_VALVE
    elif not pump and not valve:
        return 0
    else:
        return None

# Generate noise to make it more realistic
def generate_noise(lower=-2, upper=2):
    return stats.truncnorm(lower, upper, loc=(upper + lower) / 2, scale=(upper - lower) / 6).rvs()

# Get status of water level with noise included
def get_sensor(water_level):
    noise = generate_noise()
    return water_level + noise if water_level + noise > 0 else 0

# Plot results in graph various types of attack
def generate_plot(estimated_measurements, sensor_measurements, pump_status, valve_status, title=("NONE", False)):
    print("actual_measurements must have the same length as sensor_measurements" if len(estimated_measurements)!=len(sensor_measurements) else "")
    if SHOW_PLOTS or SAVE_PLOTS:
        fig, axs = plt.subplots(2, figsize=(12, 8))
        axs[0].set_title("Raw sensor measurements (Attack type: %s) (Multipoint: %s)" % title)
        axs[0].plot(estimated_measurements, linestyle='-', linewidth=1, label="actual")
        axs[0].plot(sensor_measurements, linestyle='-', linewidth=0.8, label="sensor")
        axs[0].legend()
        axs[1].set_title("Actuators Status")
        axs[1].plot(pump_status, linestyle='-', linewidth=1, label="pump")
        axs[1].plot(valve_status, linestyle='-', linewidth=0.8, label="valve")
        axs[1].legend()
        plt.tight_layout()
        if SHOW_PLOTS:
            plt.show(block=False)
        if SAVE_PLOTS:
            if not title[1]:
                filepath = "output/ATTACK_TYPE_%s/" % (title[0])
                num_list = [int(f.split('.')[0]) for f in os.listdir(filepath) if os.path.isfile(filepath + f)]
                if not num_list:
                    num = 1
                else:
                    num = max(num_list) + 1
                fig.savefig("output/ATTACK_TYPE_%s/%s.png" % (title[0], num))
            else:
                filepath = "output/ATTACK_TYPE_%s/MULTIPOINT/" % (title[0])
                num_list = [int(f.split('.')[0]) for f in os.listdir(filepath) if os.path.isfile(filepath + f)]
                if not num_list:
                    num = 1
                else:
                    num = max(num_list) + 1
                fig.savefig("output/ATTACK_TYPE_%s/MULTIPOINT/%s.png" % (title[0], num))
            plt.close()
    return

# Start simulation without attack
def run_simulation(timer, attack_type=ATTACK_TYPES[0], attack_start=0, attack_end=0, attack_param=0,attack_p_and_v=False):
    # Setting initial variables
    water_level = INITIAL_WATER_LEVEL
    estimated_measurements = []
    sensor_measurements = []
    pump_status = []
    valve_status = []
    sensor_water_level = water_level
    # setting the label for attack; 0 for no attack, 1 for attack
    attack_labels = []
    for counter in range(timer):
        # attack: boolean value that denotes whether an attack had occured, initialized to be False each iteration
        attack = False
        # Check water_level and control pump and valve accordingly
        pump, valve = get_p_and_v(sensor_water_level)
        if attack_p_and_v and counter in range(attack_start, attack_end):
            pump = not pump
            valve = not valve
        # Get rate of flow based on pump and valve status
        rate = get_rate(pump, valve)
        # New water_level
        water_level += rate
        # sensor measures water_level
        sensor_water_level = get_sensor(water_level)
        if attack_type == "BIAS":
            if counter in range(attack_start, attack_end):
                sensor_water_level += attack_param
                attack = True
        elif attack_type == "SURGE":
            if counter in range(attack_start, attack_end):
                sensor_water_level = attack_param
                attack = True
        elif attack_type == "RANDOM":
            if counter in range(attack_start, attack_end):
                sensor_water_level += random.randrange(attack_param[0], attack_param[1])
                attack = True
        # Save measurements into lists
        estimated_measurements.append(water_level)
        sensor_measurements.append(round(sensor_water_level, 2))
        pump_status.append(int(pump))
        valve_status.append(int(valve))
        # Appending the label according to whether attack is set to True or False
        if attack:
            attack_labels.append(1)
        else:
            attack_labels.append(0)
    return attack_type, attack_p_and_v, estimated_measurements, sensor_measurements, pump_status, valve_status, attack_labels

#Start simulation with attack
def run_simulations_with_attacks():
    # initialise simulator variables
    bias = [-10, 10]
    attack_type = ATTACK_TYPES[0]
    attacks = attack_start = attack_end = attack_param = 0
    attack_p_and_v = False
    attack_selection = random.randint(0, len(ATTACK_TYPES) - 1)
    attack_type = ATTACK_TYPES[attack_selection]
    attack_p_and_v = False
    if attack_type == "BIAS":
        # Time and duration of attacks are randomly generated
        attack_start = random.randint(0, 300)
        attack_duration = random.randint(1, 100)
        attack_end = attack_start + attack_duration
        attack_param = 0
        while attack_param == 0:
            attack_param = random.randint(bias[0], bias[1])
        attack_p_and_v = bool(random.randint(0, 1))
    elif attack_type == "SURGE":
        attack_start = random.randint(0, 300)
        attack_duration = random.randint(1, 100)
        attack_end = attack_start + attack_duration
        attack_param = 800
        attack_p_and_v = bool(random.randint(0, 1))
    elif attack_type == "RANDOM":
        attack_start = random.randint(0, 300)
        attack_duration = random.randint(1, 100)
        attack_end = attack_start + attack_duration
        attack_param = (-10, 10)
        attack_p_and_v = bool(random.randint(0, 1))
    if attack_selection:
        attacks += 1
        if DEBUG:
            print("Attack type: %s" % attack_type)
            print("Attack value: %s" % str(attack_param))
            print("Attack started at t: %s" % attack_start)
            print("Attack ended at t: %s" % attack_end)
            print(attack_type+" MULTIPOINT ATTACK" if attack_p_and_v == 1 else "")
    else:
        if DEBUG:
            print("Normal operation. No attack simulated.")
    attack_type,attack_p_and_v,estimated_measurements,sensor_measurements, pump_status, valve_status, attack_labels = run_simulation(SIMULATION_TIME, attack_type, attack_start,attack_end, attack_param, attack_p_and_v)
    generate_plot(estimated_measurements, sensor_measurements, pump_status, valve_status, title=(attack_type, attack_p_and_v))
    if SHOW_PLOTS:
        if RUNS > 10:
            print("Can only show plots for at most 10 runs.")
        else:
            plt.show()
    return sensor_measurements,pump_status,valve_status,attacks, attack_labels

if __name__ == "__main__":
    if DEBUG:
        init_folders()
        for i in range(RUNS):
            #Print progress of each simulation
            print("\n******  Simulation Run #%s done******" % (i + 1))
            sensor_measurements, pump_status, valve_status,attacks, attack_labels = run_simulations_with_attacks()
            df = pd.DataFrame({"pump": pump_status, "valve": valve_status, "sensor": sensor_measurements, "attack": attack_labels})
            if i>0 or os.path.isfile("output/results.csv") and os.stat("output/results.csv").st_size != 0:
                df.to_csv("output/results.csv", mode='a', index=False,header=False)
            else:
                df.to_csv("output/results.csv",index=False)
    else:
        init_folders()
        start = timer()
        for i in range(RUNS):
            sensor_measurements, pump_status, valve_status,attacks, attack_labels = run_simulations_with_attacks()
            count_danger_tank = count_danger_pump = 0
            for j in range(len(sensor_measurements)):
                if(sensor_measurements[j] > 810):
                    count_danger_tank += 1
                if(sensor_measurements[j] < 500):
                    count_danger_pump += 1
            if count_danger_tank > 1:
                print('*** Tank have overflowed for %s simulation steps***'%(count_danger_tank))
            if count_danger_pump > 1:
                print('*** Pump have dry ran for %s simulation steps***'%(count_danger_pump))
            df = pd.DataFrame({"pump": pump_status, "valve": valve_status, "sensor": sensor_measurements, "attack": attack_labels})
            if i>0 or os.path.isfile("output/results.csv") and os.stat("output/results.csv").st_size != 0:
                df.to_csv("output/results.csv", mode='a', index=False,header=False)
            else:
                df.to_csv("output/results.csv",index=False)
            # Print progress of each run
            print("****** Simulation Run #%s done ******" % (i + 1))
        end = timer()
        print("\nNumber of simulation with attacks: %s\nTime elapsed %s seconds" %(attacks,end-start))
