"""
Fast Transformer Cache Analysis Configuration for gem5
This configuration uses the traditional m5 interface for reliable simulation
"""
import os
import sys

import m5
from m5.objects import *

# Cache configuration parameters
class FastTransformerCacheConfig:
    def __init__(self):
        # Fast transformer binary path
        self.binary_path = '/home/sieni/Desktop/working_doc/project/CPU_sims/CPU_sim/gem5/sieni/fast_transformer'
        
        # Cache configuration
        self.l1i_size = '16kB'
        self.l1i_assoc = 2
        self.l1d_size = '16kB'
        self.l1d_assoc = 2
        self.l2_size = '64kB'
        self.l2_assoc = 4
        
        # Cache latencies
        self.l1_latency = '2ns'
        self.l2_latency = '20ns'
        
        # Memory configuration
        self.mem_range = '512MB'

def create_system():
    """Create the gem5 system with caches"""
    
    # Create the system
    system = System()
    system.clk_domain = SrcClockDomain()
    system.clk_domain.clock = '1GHz'
    system.clk_domain.voltage_domain = VoltageDomain()
    
    # Set memory mode and range
    system.mem_mode = 'timing'
    system.mem_ranges = [AddrRange('512MB')]
    
    # Create CPU
    system.cpu = TimingSimpleCPU()
    
    # Create cache hierarchy
    system.cpu.icache = Cache(size='16kB', assoc=2, tag_latency=2, data_latency=2, response_latency=2, mshrs=4, tgts_per_mshr=20)
    system.cpu.dcache = Cache(size='16kB', assoc=2, tag_latency=2, data_latency=2, response_latency=2, mshrs=4, tgts_per_mshr=20)
    
    # Connect caches to CPU
    system.cpu.icache.cpu_side = system.cpu.icache_port
    system.cpu.dcache.cpu_side = system.cpu.dcache_port
    
    # Create L2 cache
    system.l2cache = Cache(size='64kB', assoc=4, tag_latency=20, data_latency=20, response_latency=20, mshrs=20, tgts_per_mshr=12)
    
    # Create L2 bus
    system.l2bus = L2XBar()
    
    # Connect L1 caches to L2 bus
    system.cpu.icache.mem_side = system.l2bus.cpu_side_ports
    system.cpu.dcache.mem_side = system.l2bus.cpu_side_ports
    
    # Connect L2 cache
    system.l2cache.cpu_side = system.l2bus.mem_side_ports
    
    # Create memory bus
    system.membus = SystemXBar()
    
    # Connect L2 to memory bus
    system.l2cache.mem_side = system.membus.cpu_side_ports
    
    # Connect CPU interrupt ports
    system.cpu.createInterruptController()
    system.cpu.interrupts[0].pio = system.membus.mem_side_ports
    system.cpu.interrupts[0].int_requestor = system.membus.cpu_side_ports
    system.cpu.interrupts[0].int_responder = system.membus.mem_side_ports
    
    # Create memory controller
    system.mem_ctrl = MemCtrl()
    system.mem_ctrl.dram = DDR3_1600_8x8()
    system.mem_ctrl.dram.range = system.mem_ranges[0]
    system.mem_ctrl.port = system.membus.mem_side_ports
    
    # Connect system port
    system.system_port = system.membus.cpu_side_ports
    
    return system

def run_simulation():
    """Run the fast transformer simulation"""
    
    # Check if binary exists
    config = FastTransformerCacheConfig()
    if not os.path.exists(config.binary_path):
        print(f"Error: Binary not found at {config.binary_path}")
        print("Please compile first: make clean && make fast")
        sys.exit(1)
    
    # Create system
    system = create_system()
    
    # Set up the workload
    process = Process()
    process.cmd = [config.binary_path]
    system.cpu.workload = process
    system.cpu.createThreads()
    
    # Instantiate the system
    root = Root(full_system=False, system=system)
    m5.instantiate()
    
    print("Starting Fast Transformer Cache Analysis...")
    print(f"Binary: {config.binary_path}")
    print("Cache Configuration:")
    print(f"  L1I: {config.l1i_size}, {config.l1i_assoc}-way")
    print(f"  L1D: {config.l1d_size}, {config.l1d_assoc}-way") 
    print(f"  L2:  {config.l2_size}, {config.l2_assoc}-way")
    print("")
    
    # Start simulation
    exit_event = m5.simulate()
    
    print(f"Simulation completed: {exit_event.getCause()}")
    
    # Print basic statistics
    print("\n" + "="*50)
    print("CACHE ANALYSIS RESULTS")
    print("="*50)
    
    # Access cache statistics
    try:
        l1d_hits = system.cpu.dcache.overallHits
        l1d_misses = system.cpu.dcache.overallMisses
        l1d_accesses = l1d_hits + l1d_misses
        l1d_hit_rate = (l1d_hits / l1d_accesses * 100) if l1d_accesses > 0 else 0
        
        l1i_hits = system.cpu.icache.overallHits
        l1i_misses = system.cpu.icache.overallMisses
        l1i_accesses = l1i_hits + l1i_misses
        l1i_hit_rate = (l1i_hits / l1i_accesses * 100) if l1i_accesses > 0 else 0
        
        l2_hits = system.l2cache.overallHits
        l2_misses = system.l2cache.overallMisses
        l2_accesses = l2_hits + l2_misses
        l2_hit_rate = (l2_hits / l2_accesses * 100) if l2_accesses > 0 else 0
        
        print(f"L1D Cache - Hits: {l1d_hits}, Misses: {l1d_misses}, Hit Rate: {l1d_hit_rate:.2f}%")
        print(f"L1I Cache - Hits: {l1i_hits}, Misses: {l1i_misses}, Hit Rate: {l1i_hit_rate:.2f}%")
        print(f"L2 Cache  - Hits: {l2_hits}, Misses: {l2_misses}, Hit Rate: {l2_hit_rate:.2f}%")
        
        total_hits = l1d_hits + l1i_hits + l2_hits
        total_misses = l1d_misses + l1i_misses + l2_misses
        total_accesses = total_hits + total_misses
        overall_hit_rate = (total_hits / total_accesses * 100) if total_accesses > 0 else 0
        
        print(f"Overall   - Hits: {total_hits}, Misses: {total_misses}, Hit Rate: {overall_hit_rate:.2f}%")
        
    except AttributeError as e:
        print(f"Statistics access error: {e}")
        print("Full statistics are available in m5out/stats.txt")
    
    print("="*50)
    print("Simulation completed successfully!")
    print("Detailed statistics saved to m5out/stats.txt")

if __name__ == '__main__':
    run_simulation() 