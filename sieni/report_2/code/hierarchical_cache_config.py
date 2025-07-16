"""
Hierarchical Cache Configuration for Fast Transformer Analysis
This configuration implements a proper cache hierarchy: L1I + L1D + L2
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

# Create L1 Instruction Cache
system.cpu.icache = Cache(
    size='16kB',
    assoc=2,
    tag_latency=2,
    data_latency=2,
    response_latency=2,
    mshrs=4,
    tgts_per_mshr=20
)

# Create L1 Data Cache
system.cpu.dcache = Cache(
    size='16kB',
    assoc=2,
    tag_latency=2,
    data_latency=2,
    response_latency=2,
    mshrs=4,
    tgts_per_mshr=20
)

# Connect the I and D cache ports of the CPU to the respective caches
system.cpu.icache_port = system.cpu.icache.cpu_side
system.cpu.dcache_port = system.cpu.dcache.cpu_side

# Create L2 Bus (connecting L1 caches to L2)
system.l2bus = L2XBar()

# Connect L1 caches to L2 bus
system.cpu.icache.mem_side = system.l2bus.cpu_side_ports
system.cpu.dcache.mem_side = system.l2bus.cpu_side_ports

# Create L2 Cache
system.l2cache = Cache(
    size='64kB',
    assoc=4,
    tag_latency=20,
    data_latency=20,
    response_latency=20,
    mshrs=20,
    tgts_per_mshr=12
)

# Connect L2 cache to L2 bus
system.l2cache.cpu_side = system.l2bus.mem_side_ports

# Create main memory bus
system.membus = SystemXBar()

# Connect L2 cache to memory bus
system.l2cache.mem_side = system.membus.cpu_side_ports

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

print("Starting Fast Transformer Cache Hierarchy Analysis...")
print(f"Binary: {binpath}")
print("")
print("Cache Hierarchy Configuration:")
print("  L1I Cache: 16kB, 2-way associative, 2ns latency")
print("  L1D Cache: 16kB, 2-way associative, 2ns latency")
print("  L2 Cache:  64kB, 4-way associative, 20ns latency")
print("  Memory:    DDR3-1600, 512MiB")
print("")

# Start the simulation
exit_event = m5.simulate()

print(f"Simulation completed @ tick {m5.curTick()}")
print(f"Exit reason: {exit_event.getCause()}")
print("")
print("="*60)
print("HIERARCHICAL CACHE ANALYSIS COMPLETED")
print("="*60)

# Print cache statistics summary
try:
    # L1I Cache Stats
    l1i_hits = system.cpu.icache.overallHits
    l1i_misses = system.cpu.icache.overallMisses
    l1i_accesses = l1i_hits + l1i_misses
    l1i_hit_rate = (l1i_hits / l1i_accesses * 100) if l1i_accesses > 0 else 0
    
    # L1D Cache Stats
    l1d_hits = system.cpu.dcache.overallHits
    l1d_misses = system.cpu.dcache.overallMisses
    l1d_accesses = l1d_hits + l1d_misses
    l1d_hit_rate = (l1d_hits / l1d_accesses * 100) if l1d_accesses > 0 else 0
    
    # L2 Cache Stats
    l2_hits = system.l2cache.overallHits
    l2_misses = system.l2cache.overallMisses
    l2_accesses = l2_hits + l2_misses
    l2_hit_rate = (l2_hits / l2_accesses * 100) if l2_accesses > 0 else 0
    
    print("Cache Performance Summary:")
    print(f"  L1I: {l1i_hits:,} hits, {l1i_misses:,} misses, {l1i_hit_rate:.2f}% hit rate")
    print(f"  L1D: {l1d_hits:,} hits, {l1d_misses:,} misses, {l1d_hit_rate:.2f}% hit rate")
    print(f"  L2:  {l2_hits:,} hits, {l2_misses:,} misses, {l2_hit_rate:.2f}% hit rate")
    
    # Overall statistics
    total_l1_hits = l1i_hits + l1d_hits
    total_l1_misses = l1i_misses + l1d_misses
    total_l1_accesses = total_l1_hits + total_l1_misses
    overall_l1_hit_rate = (total_l1_hits / total_l1_accesses * 100) if total_l1_accesses > 0 else 0
    
    print("")
    print(f"Overall L1 Hit Rate: {overall_l1_hit_rate:.2f}%")
    print(f"L2 Local Hit Rate: {l2_hit_rate:.2f}%")
    
except AttributeError as e:
    print(f"Note: Live statistics not available during simulation")
    print("Complete cache hierarchy statistics available in m5out/stats.txt")

print("")
print("Detailed cache hierarchy statistics: m5out/stats.txt")
print("Configuration details: m5out/config.ini")
print("="*60) 