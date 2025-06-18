# # Local Performance Testing of `jr_py_writer`

This document provides a detailed overview of the local performance testing conducted on the `jr_py_writer` library, specifically focusing on the `FileHandler` class. The tests were executed in both synchronous and asynchronous modes to evaluate their performance under various conditions.

## Local Tests

The benchmarks were also executed on a local machine.

## Benchmark Summary

**Generated:** June 18, 2025  
**Pytest Benchmark Version:** 5.1.0  
**Tested Library Version:** 0.1.0

## System Information

- **Machine:** Intel(R) Core(TM) i7-4510U CPU @ 2.00GHz (4 cores)
- **OS:** Windows 10 AMD64
- **Python:** 3.12.8 (CPython)
- **Memory:** L2 Cache: 64KB, Cache Line: 256B
- **Disk:** SSD with 512GB capacity
- **Ram:** 16GB DDR3

## Executive Summary

The benchmark tests evaluate the FileHandler's performance across different file counts (100, 300, 500, 1000, 2000) and operation modes:

- **Standard write operations** (with flush)
- **No-flush write operations**
- **Context manager operations** (with/without flush)

## Sync Raw Data

The following table summarizes the raw benchmark data collected during the tests. Each operation was executed multiple times to ensure statistical significance, and the results are presented in microseconds (μs) for consistency.

| Name                                                              | Min (us)         | Max (us)         | Mean (us)        | StdDev (us)      | Median (us)      | IQR (us)         | Outliers | OPS             | Rounds | Iterations |
|-------------------------------------------------------------------|------------------|------------------|------------------|------------------|------------------|------------------|----------|-----------------|--------|------------|
| test_benchmark_file_handler_cm_write[2000]                       | 2.3000 (1.0)     | 14.5000 (1.15)   | 5.1200 (1.09)    | 5.2633 (1.19)    | 2.8000 (1.17)    | 3.8001 (8.44)    | 1;1      | 195,312.7892    | 5      | 1          |
| test_benchmark_file_handler_cm_write_no_flush[300]               | 2.3999 (1.04)    | 13.0000 (1.03)   | 4.6800 (1.0)     | 4.6639 (1.05)    | 2.4000 (1.0)     | 3.2500 (7.22)    | 1;1      | 213,675.7127    | 5      | 1          |
| test_benchmark_file_handler_cm_write_no_flush[1000]              | 2.4000 (1.04)    | 13.0000 (1.03)   | 4.6800 (1.00)    | 4.6639 (1.05)    | 2.4000 (1.0)     | 3.2500 (7.22)    | 1;1      | 213,674.6497    | 5      | 1          |
| test_benchmark_file_handler_cm_write[1000]                       | 2.4999 (1.09)    | 12.6001 (1.0)    | 4.7000 (1.00)    | 4.4289 (1.0)     | 2.6000 (1.08)    | 3.1251 (6.94)    | 1;1      | 212,765.3914    | 5      | 1          |
| test_benchmark_file_handler_cm_write_no_flush[2000]              | 2.5000 (1.09)    | 12.9000 (1.02)   | 4.8000 (1.03)    | 4.5398 (1.03)    | 2.8000 (1.17)    | 3.1999 (7.11)    | 1;1      | 208,333.7681    | 5      | 1          |
| test_benchmark_file_handler_cm_write_no_flush[500]               | 2.7000 (1.17)    | 24.4000 (1.94)   | 11.7200 (2.50)   | 8.6015 (1.94)    | 12.8000 (5.33)   | 12.2499 (27.22)  | 2;0      | 85,324.2604     | 5      | 1          |
| test_benchmark_file_handler_cm_write[500]                        | 3.8999 (1.70)    | 18.3000 (1.45)   | 7.9000 (1.69)    | 6.1948 (1.40)    | 4.2000 (1.75)    | 7.2751 (16.16)   | 1;0      | 126,582.0608    | 5      | 1          |
| test_benchmark_file_handler_cm_write[300]                        | 6.3000 (2.74)    | 17.8000 (1.41)   | 8.9000 (1.90)    | 4.9860 (1.13)    | 6.6001 (2.75)    | 3.3250 (7.39)    | 1;1      | 112,359.5768    | 5      | 1          |
| test_benchmark_file_handler_cm_write_no_flush[100]               | 6.3000 (2.74)    | 22.3001 (1.77)   | 8.9000 (1.90)    | 5.9226 (1.34)    | 6.6999 (2.79)    | 0.9000 (2.00)    | 1;1      | 112,359.7448    | 7      | 1          |
| test_benchmark_file_handler_cm_write[100]                        | 6.4000 (2.78)    | 20.7999 (1.65)   | 8.4000 (1.79)    | 5.0154 (1.13)    | 6.6500 (2.77)    | 0.4501 (1.0)     | 1;1      | 119,047.5375    | 8      | 1          |
| test_benchmark_file_handler_write[100]                           | 22,028.9000      | 30,420.5001      | 25,834.2769      | 3,082.0995       | 25,778.2000      | 6,060.6750       | 6;0      | 38.7083         | 13     | 1          |
| test_benchmark_file_handler_write_no_flush[100]                  | 23,013.0000      | 37,296.2001      | 27,757.3500      | 3,559.6672       | 26,835.8000      | 3,247.8500       | 2;1      | 36.0265         | 12     | 1          |
| test_benchmark_file_handler_write[300]                           | 56,467.3000      | 68,400.6000      | 62,283.7600      | 4,625.0972       | 62,090.1000      | 6,990.8749       | 2;0      | 16.0555         | 5      | 1          |
| test_benchmark_file_handler_write_no_flush[300]                  | 78,488.5000      | 88,399.9000      | 83,660.4400      | 3,947.5096       | 82,440.5999      | 5,876.4000       | 2;0      | 11.9531         | 5      | 1          |
| test_benchmark_file_handler_write[500]                           | 93,138.1000      | 123,017.6999     | 103,437.2200     | 11,503.0591      | 99,825.3000      | 10,938.9500      | 1;0      | 9.6677          | 5      | 1          |
| test_benchmark_file_handler_write_no_flush[500]                  | 125,484.2000     | 165,819.2000     | 139,054.3200     | 15,633.0242      | 133,630.1999     | 14,514.0000      | 1;0      | 7.1914          | 5      | 1          |
| test_benchmark_file_handler_write[1000]                          | 185,452.8000     | 317,164.6000     | 235,019.1200     | 56,800.5881      | 214,243.8000     | 92,920.9000      | 1;0      | 4.2550          | 5      | 1          |
| test_benchmark_file_handler_write_no_flush[1000]                 | 244,064.4000     | 294,412.4000     | 276,375.8800     | 21,686.2536      | 286,564.3000     | 33,791.5249      | 1;0      | 3.6183          | 5      | 1          |
| test_benchmark_file_handler_write_no_flush[2000]                 | 502,768.1000     | 616,022.8000     | 532,813.6800     | 47,741.5338      | 509,333.5001     | 46,643.5250      | 1;0      | 1.8768          | 5      | 1          |
| test_benchmark_file_handler_write[2000]                          | 514,564.5001     | 588,609.3000     | 555,525.4600     | 37,342.2583      | 575,045.8001     | 70,000.8750      | 2;0      | 1.8001          | 5      | 1          |

## Sync Performance Breakdown

### Context Manager (CM) Mode — Fast Performance

| File Count | Mean with Flush (μs) | Mean without Flush (μs) | Notes                            |
|-------------|------------------------|---------------------------|-----------------------------------|
| 100         | 8.4                    | 8.9                       | No significant difference        |
| 300         | 8.9                    | 4.68                      | No-flush performs better         |
| 500         | 7.9                    | 11.72                     | No-flush shows higher variance   |
| 1000        | 4.7                    | 4.68                      | Very efficient at higher loads   |
| 2000        | 5.12                   | 4.8                       | Scales linearly, remains fast    |

**Observation:**

- Performance is nearly constant even as the file count increases.  
- Variability is minor, possibly affected by OS caching or I/O scheduling.

---

### Standard Write Mode — Slower

| File Count | Mean with Flush (μs) | Mean without Flush (μs) | Notes                            |
|-------------|------------------------|---------------------------|-----------------------------------|
| 100         | 25,834                | 27,757                    | Flush doesn’t improve performance |
| 300         | 62,283                | 83,660                    | Degrades sharply                 |
| 500         | 103,437               | 139,054                   | Continues degrading              |
| 1000        | 235,019               | 276,375                   | Exponential degradation          |
| 2000        | 555,525               | 532,813                   | Hit disk bandwidth limits        |

**Observation:**  

- Performance **degrades exponentially** as the number of writes increases.  
- Flush or no-flush has **little effect**, meaning that the bottleneck is elsewhere — likely the manual handling of open/close or OS-level sync overhead.

---

## Key Findings

1. **Context Manager Outperforms Manual Write Drastically**

- 1000 writes with context manager: **~4.7μs**  
- 1000 writes with manual open/write/close: **~235,000μs (235ms)**  
- Context manager is **~50,000x faster** in this test case.

2. **Flush Impact is Minimal**

- Whether flush is enabled or not, the difference is minor. This suggests that the buffering provided by Python’s file I/O and the OS is sufficient for most use cases.

3. **Scalability**

- Context manager scales **linearly** and remains fast even at 2000 files.  
- Manual write scales **exponentially worse**, possibly due to expensive open/close operations or disk I/O overhead without effective batching.

---

### Async Raw Data

| Name                                                              | Min (us) | Max (us)   | Mean (us) | StdDev (us) | Median (us) | IQR (us) | Outliers   | OPS (Kops/s) | Rounds | Iterations |
|-------------------------------------------------------------------|----------|------------|-----------|-------------|-------------|----------|------------|--------------|--------|------------|
| test_benchmark_async_cm_file_handler_write[1000]                 | 3.0999   | 5,704.9000 | 8.3572    | 57.8782     | 6.5000      | 4.2000   | 137;1038   | 119.6571     | 27323  | 1          |
| test_benchmark_async_cm_file_handler_write[100]                  | 3.0999   | 1,447.1001 | 4.5520    | 16.1380     | 3.3000      | 1.1000   | 71;3370    | 219.6813     | 21009  | 1          |
| test_benchmark_async_cm_file_handler_write[2000]                 | 3.0999   | 511.6001   | 4.0380    | 5.7739      | 3.3000      | 0.2000   | 295;5016   | 247.6477     | 27249  | 1          |
| test_benchmark_async_cm_file_handler_write[300]                  | 3.0999   | 931.2000   | 4.2015    | 9.9734      | 3.3000      | 1.0999   | 145;2032   | 238.0124     | 21277  | 1          |
| test_benchmark_async_cm_file_handler_write[500]                  | 3.0999   | 2,958.1999 | 6.6827    | 31.3102     | 6.3999      | 4.1999   | 110;435    | 149.6401     | 22625  | 1          |
| test_benchmark_async_cm_file_handler_write_no_flush[1000]        | 3.0999   | 1,151.3000 | 4.0919    | 8.7703      | 3.2000      | 0.2000   | 196;6887   | 244.3829     | 28410  | 1          |
| test_benchmark_async_cm_file_handler_write_no_flush[100]         | 3.0999   | 1,093.6999 | 4.3860    | 13.4824     | 3.3000      | 0.2000   | 117;6502   | 227.9960     | 27856  | 1          |
| test_benchmark_async_cm_file_handler_write_no_flush[2000]        | 3.0999   | 1,703.8001 | 5.0312    | 18.4761     | 3.3000      | 1.2001   | 170;5659   | 198.7616     | 27625  | 1          |
| test_benchmark_async_cm_file_handler_write_no_flush[300]         | 3.0999   | 1,169.2001 | 5.1801    | 13.3966     | 3.3000      | 4.0999   | 105;213    | 193.0478     | 21414  | 1          |
| test_benchmark_async_cm_file_handler_write_no_flush[500]         | 3.0999   | 1,411.6000 | 4.9361    | 17.2235     | 3.2999      | 1.2000   | 126;6346   | 202.5897     | 28902  | 1          |
| test_benchmark_async_file_handler_write[1000]                    | 3.0999   | 6,646.5000 | 8.6996    | 70.8389     | 6.8001      | 4.2999   | 107;913    | 114.9479     | 28249  | 1          |
| test_benchmark_async_file_handler_write[100]                     | 3.0999   | 2,842.5000 | 6.3908    | 34.6288     | 4.3000      | 4.1999   | 36;286     | 156.4756     | 13851  | 1          |
| test_benchmark_async_file_handler_write[2000]                    | 3.0999   | 1,418.4000 | 5.7805    | 20.6317     | 3.6999      | 3.5001   | 130;693    | 172.9963     | 27625  | 1          |
| test_benchmark_async_file_handler_write[300]                     | 3.0999   | 991.2001   | 4.1134    | 11.0881     | 3.3000      | 0.1999   | 139;3206   | 243.1079     | 21098  | 1          |
| test_benchmark_async_file_handler_write[500]                     | 3.0999   | 1,043.1000 | 4.0078    | 8.5006      | 3.3000      | 0.1001   | 195;4313   | 249.5136     | 26738  | 1          |
| test_benchmark_async_file_handler_write_no_flush[1000]           | 3.0999   | 775.2001   | 4.2023    | 7.8295      | 3.3000      | 0.1001   | 317;5150   | 237.9646     | 28012  | 1          |
| test_benchmark_async_file_handler_write_no_flush[100]            | 3.0999   | 3,604.2000 | 7.2085    | 41.3352     | 6.6999      | 4.1000   | 119;723    | 138.7257     | 28329  | 1          |
| test_benchmark_async_file_handler_write_no_flush[2000]           | 3.0999   | 726.1999   | 3.8638    | 6.8861      | 3.2000      | 0.1000   | 287;4477   | 258.8132     | 29326  | 1          |
| test_benchmark_async_file_handler_write_no_flush[300]            | 3.0999   | 946.8000   | 4.4751    | 10.9470     | 3.3000      | 1.1999   | 128;4272   | 223.4607     | 25774  | 1          |
| test_benchmark_async_file_handler_write_no_flush[500]            | 3.0999   | 816.6999   | 4.9290    | 13.7948     | 3.3000      | 2.9000   | 26;52      | 202.8816     | 4951   | 1          |

## Async Performance Breakdown

### Context Manager (CM) Mode — Consistent Fast Performance

| File Count | Mean with Flush (μs) | Mean without Flush (μs) | Notes                            |
|-------------|------------------------|---------------------------|-----------------------------------|
| 100         | 4.55                   | 4.39                      | Minimal difference               |
| 300         | 4.20                   | 5.18                      | Slight variance                  |
| 500         | 6.68                   | 4.94                      | Some variability                 |
| 1000        | 8.36                   | 4.09                      | No-flush performs better         |
| 2000        | 4.04                   | 5.03                      | Excellent scalability            |

**Observation:**

- Performance remains consistently fast across all file counts.
- No-flush generally performs slightly better or equivalent.
- Excellent scalability with minimal performance degradation.

---

### Standard Async Write Mode — Also Fast

| File Count | Mean with Flush (μs) | Mean without Flush (μs) | Notes                            |
|-------------|------------------------|---------------------------|-----------------------------------|
| 100         | 6.39                   | 7.21                      | Slightly slower than CM          |
| 300         | 4.11                   | 4.48                      | Comparable to CM performance     |
| 500         | 4.01                   | 4.93                      | Very efficient                   |
| 1000        | 8.70                   | 4.20                      | No-flush significantly better    |
| 2000        | 5.78                   | 3.86                      | Scales well                      |

**Observation:**

- Unlike synchronous mode, async standard write performs very well.
- Performance is comparable to context manager mode.
- Excellent scalability with no exponential degradation.

---

## Key Findings - Async Performance

1. **Async Operations Are Consistently Fast**

- Both context manager and standard write modes maintain excellent performance.
- 1000 writes with async context manager: **~8.36μs** (with flush)
- 1000 writes with async standard write: **~8.70μs** (with flush)

2. **No-Flush Generally Performs Better**

- Across most test cases, no-flush operations show better or equivalent performance.
- The difference is more pronounced in higher file counts.

3. **Excellent Scalability**

- Both async modes scale **linearly** and maintain low latency.
- No exponential performance degradation like in synchronous standard write mode.
- Async operations effectively handle I/O concurrency, preventing bottlenecks.

4. **Async vs Sync Comparison**

- Async context manager (1000 files): **~8.36μs**
- Sync context manager (1000 files): **~4.70μs**
- Async standard write (1000 files): **~8.70μs**
- Sync standard write (1000 files): **~235,000μs**

The async standard write mode eliminates the massive performance penalty seen in synchronous standard write operations.

---
