"""
Working Fast Transformer Cache Analysis Configuration for gem5
Based on the successful learning_gem5/part2/simple_cache.py pattern
"""

import os
import m5
from m5.objects import *

# Create the system we are going to simulate
system = System()

# Set the clock frequency of the system (and all of its children)
system.clk_domain = SrcClockDomain()
system.clk_domain.clock = "1GHz"
system.clk_domain.voltage_domain = VoltageDomain()

# Set up the system
system.mem_mode = "timing"  # Use timing accesses
system.mem_ranges = [AddrRange("512MiB")]  # Create an address range

# Create a simple CPU (use X86TimingSimpleCPU for X86 binaries)
system.cpu = X86TimingSimpleCPU()

# Create a memory bus, a coherent crossbar, in this case
system.membus = SystemXBar()

# Create a simple cache with reasonable size for transformer analysis
system.cache = SimpleCache(size="64KiB")

# Connect the I and D cache ports of the CPU to the cache
system.cpu.icache_port = system.cache.cpu_side
system.cpu.dcache_port = system.cache.cpu_side

# Hook the cache up to the memory bus
system.cache.mem_side = system.membus.cpu_side_ports

# Create the interrupt controller for the CPU and connect to the membus
system.cpu.createInterruptController()
system.cpu.interrupts[0].pio = system.membus.mem_side_ports
system.cpu.interrupts[0].int_requestor = system.membus.cpu_side_ports
system.cpu.interrupts[0].int_responder = system.membus.mem_side_ports

# Create a DDR3 memory controller and connect it to the membus
system.mem_ctrl = MemCtrl()
system.mem_ctrl.dram = DDR3_1600_8x8()
system.mem_ctrl.dram.range = system.mem_ranges[0]
system.mem_ctrl.port = system.membus.mem_side_ports

# Connect the system up to the membus
system.system_port = system.membus.cpu_side_ports

# Create a process for our fast transformer application
process = Process()

# Set the command to our fast transformer binary
thispath = os.path.dirname(os.path.realpath(__file__))
binpath = os.path.join(thispath, "fast_transformer")

# Verify the binary exists
if not os.path.exists(binpath):
    print(f"Error: Binary not found at {binpath}")
    print("Please build the fast transformer first: make fast")
    exit(1)

# cmd is a list which begins with the executable (like argv)
process.cmd = [binpath]

# Set the cpu to use the process as its workload and create thread contexts
system.cpu.workload = process
system.cpu.createThreads()

# Set up the workload
system.workload = SEWorkload.init_compatible(binpath)

# Set up the root SimObject and start the simulation
root = Root(full_system=False, system=system)

# Instantiate all of the objects we've created above
m5.instantiate()

print("Starting Fast Transformer Cache Analysis...")
print(f"Binary: {binpath}")
print("Cache Configuration: 64KiB SimpleCache")
print("")

# Start the simulation
exit_event = m5.simulate()

print(f"Simulation completed @ tick {m5.curTick()}")
print(f"Exit reason: {exit_event.getCause()}")
print("")
print("="*50)
print("CACHE ANALYSIS COMPLETED")
print("="*50)
print("Detailed statistics available in: m5out/stats.txt")
print("Configuration details in: m5out/config.ini")
print("="*50) 