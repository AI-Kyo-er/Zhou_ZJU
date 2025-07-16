# Transformer Cache Hierarchy Analysis using gem5 Simulator

## Executive Summary

我们已经进行的探究集中在 LLM 训练推理 以及 CPU simulation and profiling 上。因此我做了结合，本报告使用 gem5 分析了 Transformer 神经网络推理的缓存层次结构性能。该研究使用 C++ 实现了一个简化的 Transformer，并评估了不同缓存配置下的内存访问模式。结果显示，Transformer 具有出色的缓存局部性，在分层配置下实现了 99.42% 的 L1 命中率。

## 1. Introduction and Test Overview

### 1.1 Research Objective

This study analyzes cache hierarchy behavior of Transformer neural networks during inference operations. Understanding cache access patterns of attention mechanisms and matrix computations is crucial for optimizing hardware designs and improving inference performance.

### 1.2 Test Methodology

The analysis uses gem5 to simulate different cache configurations while executing a custom Transformer model. Two configurations are compared:

- **Unified Cache Configuration**: Single 64KB SimpleCache for both instruction and data requests
- **Hierarchical Cache Configuration**: Three-level hierarchy with separate L1I (16KB), L1D (16KB), and unified L2 cache (64KB)

## 2. Implementation Architecture

### 2.1 Transformer Implementation (`mini_transformer.cpp`)

考虑到 python interpreter 存在的额外开销，以及 python 过度包装了底层存贮、访存的细节，因此我们采用 C++ 进行典型的 Transformer self-attention 的实现。 被重点测试的代码开销体现在以下两个方面。

#### 2.1.1 Matrix Operations Foundation

The `MiniMatrix` class provides the fundamental building block:

```cpp
class MiniMatrix {
private:
    std::vector<float> data;
    int rows, cols;
    
public:
    MiniMatrix multiply(const MiniMatrix& other) const {
        MiniMatrix result(rows, other.cols);
        for (int i = 0; i < rows; i++) {
            for (int j = 0; j < other.cols; j++) {
                float sum = 0.0f;
                for (int k = 0; k < cols; k++) {
                    sum += (*this)(i, k) * other(k, j);
                }
                result(i, j) = sum;
            }
        }
        return result;
    }
};
```

Uses contiguous memory allocation via `std::vector<float>` for predictable cache behavior. The O(n³) matrix multiplication creates regular memory access patterns suitable for cache analysis.

#### 2.1.2 Attention Mechanism

The `MiniAttention` class implements the self-attention mechanism:

```cpp
class MiniAttention {
public:
    MiniMatrix forward(const MiniMatrix& input) {
        // Create simplified Q, K, V matrices
        MiniMatrix Q(seq_len, d_model);
        MiniMatrix K(seq_len, d_model);
        MiniMatrix V(seq_len, d_model);
        
        // Simplified attention scores computation
        MiniMatrix scores(seq_len, seq_len);
        for (int i = 0; i < seq_len; i++) {
            for (int j = 0; j < seq_len; j++) {
                float score = 0.0f;
                for (int k = 0; k < d_model; k++) {
                    score += Q(i, k) * K(j, k);
                }
                scores(i, j) = score / sqrt(d_model);
            }
        }
    }
};
```

Creates multiple memory access patterns: sequential access for Q, K, V creation, and complex patterns for score computation and value aggregation.

### 2.2 Unified Cache Configuration (`working_fast_config.py`)

我们首先延续 gem5 demo 中的配置，实验了 Unified Cache 下的数据收集。
Establishes baseline simulation using gem5's m5 interface:

```python
# Create a simple cache with reasonable size for transformer analysis
system.cache = SimpleCache(size="64KiB")

# Connect the I and D cache ports of the CPU to the cache
system.cpu.icache_port = system.cache.cpu_side
system.cpu.dcache_port = system.cache.cpu_side
```

Routes both instruction and data requests through a single cache, focusing on overall cache behavior. Uses `X86TimingSimpleCPU` for cycle-accurate simulation and DDR3 memory controller.

Serves as control configuration for baseline performance metrics.

### 2.3 Hierarchical Cache Configuration (`hierarchical_cache_config.py`)

为了更加真实的模拟现实中的CPU环境，我们进一步定义了一个多级缓存，并且 instruction cache 和 data cache 分立的结构。
Implements realistic three-level cache hierarchy representative of modern processors:

```python
# Create L1 Instruction Cache
system.cpu.icache = Cache(
    size='16kB', assoc=2,
    tag_latency=2, data_latency=2, response_latency=2
)

# Create L1 Data Cache
system.cpu.dcache = Cache(
    size='16kB', assoc=2,
    tag_latency=2, data_latency=2, response_latency=2
)

# Create L2 Cache
system.l2cache = Cache(
    size='64kB', assoc=4,
    tag_latency=20, data_latency=20, response_latency=20
)
```

Separates instruction and data streams at L1 level for independent locality analysis. L2 serves as unified secondary cache with realistic latency differences (2ns L1, 20ns L2).

Enables detailed cache behavior analysis at each level.

## 3. Results Analysis

### 3.1 Unified Cache Performance

Exceptional overall cache performance:

- **Cache Hit Ratio**: 97.08%
- **Total Cache Hits**: 55,828,895
- **Total Cache Misses**: 1,677,010
- **Average Miss Latency**: 38,609 ticks
- **Instructions per Cycle (CPI)**: 3.67

High hit ratio indicates strong temporal and spatial locality. Working set fits well within 64KB cache size. Low CPI demonstrates efficient execution despite memory-intensive matrix operations.

### 3.2 Hierarchical Cache Performance

Detailed cache behavior insights at each level:

#### 3.2.1 L1 Cache Performance
- **L1I (Instruction Cache)**: 99.88% hit rate (3,518,087 hits, 4,366 misses)
- **L1D (Data Cache)**: 97.51% hit rate (821,920 hits, 21,007 misses)
- **Overall L1 Hit Rate**: 99.42%

Exceptional L1I hit rate reflects repetitive Transformer computations. Lower L1D hit rate indicates diverse data access patterns from matrix operations.

#### 3.2.2 L2 Cache Performance
- **L2 Hit Rate**: 32.18% (8,167 hits, 17,214 misses)
- **Memory Traffic Reduction**: 99.61%

L2 handles L1 misses effectively. 99.61% memory traffic reduction demonstrates hierarchical design effectiveness in minimizing main memory accesses.

### 3.3 Performance Implications

从数据中我们对 transformer 结构进行合理分析如下：
#### 3.3.1 Attention Mechanism Locality

High cache hit rates indicate favorable locality characteristics. Q⊗K^T computation creates predictable access patterns aligned with cache line organization, resulting in efficient cache utilization.

#### 3.3.2 缓存预热效应的存在

Initial layer execution establishes cached patterns that subsequent layers exploit, contributing to high hit rates.

## 4. Simulator Analysis: PIN vs. gem5

今天的会议中，Dr. Wu 问到具体 gem5 和 PIN 结构的辨析，我作以下回答：
### 4.1 gem5 Characteristics

首先通过 python 代码定义的进行硬件建模，Includes detailed models of CPU cores, cache hierarchies, memory controllers, and interconnects with configurable realistic parameters.

在这个被建模的 架构上，实际模拟binary instructions的执行，Monitor信息来源于 virtual CPU 中的 virtual events 的统计。

### 4.2 PIN-based Simulator Characteristics
PIN-based 指的是 inserting analysis code at instruction boundaries, enabling detailed program analysis without source code modification.

### 4.3 Comparative Analysis for Transformer Cache Studies

各自擅长的领域不同，gem5 通过自定义的 vitual archetechture 可以辅助分析不同的架构下， LLM inference and training 的数据。而 PIN-based Simulator excels at program characterization, memory access tracing, and behavioral analysis but lacks detailed hardware timing or architectural modeling.

## 5. Conclusions

Transformer neural networks exhibit excellent cache locality characteristics when analyzed using gem5. Hierarchical cache analysis reveals L1 caches achieve near-optimal performance (99.42% hit rate), while L2 caches effectively handle capacity misses.

The implementation methodology successfully captures essential Transformer computational patterns while maintaining simulation tractability. Modular design enables future extensions for larger models and alternative configurations.

gem5 is established as the appropriate platform for cache hierarchy studies, providing necessary architectural detail and timing accuracy. This work provides foundation for future memory system optimization research for neural network inference workloads.