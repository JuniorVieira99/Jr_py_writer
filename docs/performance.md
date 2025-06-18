# Performance Metrics for `jr_py_writer`

This document provides detailed performance benchmarks for the `jr_py_writer` library, focusing on synchronous and asynchronous file handling operations.

---

## Index

- [Benchmark Results](#benchmark-results)
  - [Git Hub Actions Runner](#git-hub-actions-runner)
    - [Linux Environment](#linux-environment)
    - [Windows Environment](#windows-environment)
    - [MacOS Environment](#macos-environment)
- [Summary](#summary)
- [Testing](#testing)
- [License](#license)

## Benchmark Results

### Git Hub Actions Runner

The benchmarks were executed on a GitHub Actions virtual machine runner.

#### Linux Environment

- Linux (x64):
- Processor (CPU): AMD EPYC 7B12 processors
- Cores (CPU): 4 cores
- Memory (RAM): 16 GB
- Storage (SSD): 14 GB
- Workflow Labels: ubuntu-latest, ubuntu-24.04, ubuntu-22.04

#### Linux Environment Results

**Synchronous File Handling (`FileHandler_SYNC`)**

| Test Name                                           | Min (ns) | Max (ns) | Mean (ns) | StdDev (ns) | Median (ns) | OPS (Mops/s) | Rounds | Iterations |
|-----------------------------------------------------|----------|----------|-----------|-------------|-------------|--------------|--------|------------|
| `test_benchmark_file_handler_cm_write_no_flush[100]` | 500      | 5,792    | 663.36    | 548.97      | 583         | 1.507        | 90     | 1          |
| `test_benchmark_file_handler_cm_write[100]`         | 541      | 3,625    | 610.22    | 263.52      | 583         | 1.639        | 138    | 1          |
| `test_benchmark_file_handler_cm_write[300]`         | 542      | 3,875    | 674.16    | 490.37      | 584         | 1.483        | 45     | 1          |
| `test_benchmark_file_handler_cm_write[500]`         | 583      | 8,125    | 1,125.07  | 1,938.27    | 625         | 0.889        | 15     | 1          |
| `test_benchmark_file_handler_cm_write_no_flush[1000]` | 583      | 7,458    | 1,362.40  | 2,145.93    | 625         | 0.734        | 10     | 1          |
| `test_benchmark_file_handler_cm_write_no_flush[300]` | 583      | 5,833    | 990.24    | 1,252.05    | 666         | 1.010        | 17     | 1          |
| `test_benchmark_file_handler_cm_write_no_flush[500]` | 583      | 7,167    | 1,107.07  | 1,746.81    | 625         | 0.903        | 14     | 1          |
| `test_benchmark_file_handler_cm_write[1000]`        | 583      | 8,791    | 1,247.14  | 2,174.21    | 625         | 0.802        | 14     | 1          |
| `test_benchmark_file_handler_cm_write_no_flush[2000]` | 625      | 7,416    | 1,666.57  | 2,538.68    | 667         | 0.600        | 7      | 1          |
| `test_benchmark_file_handler_cm_write[2000]`        | 666      | 7,500    | 2,125.00  | 3,008.68    | 750         | 0.471        | 5      | 1          |

**Asynchronous File Handling (`FileHandler_ASYNC`)**

| Test Name                                           | Min (ns) | Max (ns) | Mean (ns) | StdDev (ns) | Median (ns) | OPS (Mops/s) | Rounds | Iterations |
|-----------------------------------------------------|----------|----------|-----------|-------------|-------------|--------------|--------|------------|
| `test_benchmark_async_cm_file_handler_write[300]`   | 750      | 116,458  | 890.53    | 465.66      | 875         | 1.123        | 74,767 | 1          |
| `test_benchmark_async_cm_file_handler_write[500]`   | 750      | 29,583   | 883.95    | 197.21      | 875         | 1.131        | 73,622 | 1          |
| `test_benchmark_async_cm_file_handler_write[2000]`  | 750      | 44,250   | 896.01    | 316.27      | 875         | 1.116        | 34,986 | 1          |
| `test_benchmark_async_cm_file_handler_write_no_flush[1000]` | 750 | 9,125    | 882.34    | 106.11      | 875         | 1.133        | 62,665 | 1          |
| `test_benchmark_async_cm_file_handler_write_no_flush[300]` | 750 | 15,750   | 882.60    | 144.86      | 875         | 1.133        | 64,692 | 1          |
| `test_benchmark_async_file_handler_write[1000]`     | 750      | 31,042   | 889.35    | 221.76      | 875         | 1.124        | 52,288 | 1          |
| `test_benchmark_async_file_handler_write[2000]`     | 750      | 83,625   | 896.35    | 451.24      | 875         | 1.116        | 54,178 | 1          |
| `test_benchmark_async_file_handler_write[300]`      | 750      | 295,709  | 906.44    | 1,536.78    | 875         | 1.103        | 63,160 | 1          |
| `test_benchmark_async_file_handler_write[500]`      | 750      | 91,584   | 880.61    | 429.86      | 875         | 1.136        | 59,999 | 1          |
| `test_benchmark_async_file_handler_write_no_flush[100]` | 750 | 12,625   | 889.12    | 112.00      | 875         | 1.125        | 97,163 | 1          |

#### Windows Environment

- Memory (RAM): 16 GB
- Processor (CPU): AMD EPYC 7B12 processors
- Cores (CPU): 4 cores
- Storage (SSD): 14 GB
- Workflow Labels: windows-latest, windows-2025, windows-2022, windows-2019

#### Windows Environment Results

**Synchronous File Handling (`FileHandler_SYNC`)**

**Asynchronous File Handling (`FileHandler_ASYNC`)**

#### MacOS Environment

- Memory (RAM): 7 GB
- Processor (CPU): Intel Xeon W processors.
- Cores (CPU): 3 cores
- Storage (SSD): 14 GB
- Workflow Labels: macos-latest, macos-14, macos-15

#### MacOS Environment Results

**Synchronous File Handling (`FileHandler_SYNC`)**

**Asynchronous File Handling (`FileHandler_ASYNC`)**

---

### Local Tests

The benchmarks were also executed on a local machine.

#### Local Environment

- Operating System: Windows 10
- Memory (RAM): 16 GB
- Processor (CPU): Intel Core i7-4510u
- Cores (CPU): 2 cores
- Storage (SSD): 512 GB

#### Local Environment Results

**Synchronous File Handling (`FileHandler_SYNC`)**

| Name                                                              | Min (us)       | Max (us)       | Mean (us)      | StdDev (us)    | Median (us)    | IQR (us)       | Outliers | OPS            | Rounds | Iterations |
|-------------------------------------------------------------------|----------------|----------------|----------------|----------------|----------------|----------------|----------|----------------|--------|------------|
| test_benchmark_file_handler_cm_write_no_flush[100]               | 2.2999         | 14.8000        | 3.6091         | 3.7273         | 2.4000         | 0.1500         | 1;2      | 277,077.6008   | 11     | 1          |
| test_benchmark_file_handler_cm_write_no_flush[300]               | 2.3000         | 17.2000        | 5.9000         | 6.3977         | 2.7999         | 5.5250         | 1;1      | 169,491.5726   | 5      | 1          |
| test_benchmark_file_handler_cm_write[2000]                       | 2.4000         | 13.3000        | 4.7800         | 4.7741         | 2.6000         | 3.3249         | 1;1      | 209,205.4660   | 5      | 1          |
| test_benchmark_file_handler_cm_write[500]                        | 2.4000         | 12.4000        | 4.6000         | 4.3686         | 2.6000         | 2.9499         | 1;1      | 217,391.8497   | 5      | 1          |
| test_benchmark_file_handler_cm_write[1000]                       | 4.5999         | 17.5000        | 7.3400         | 5.6871         | 4.7000         | 3.7499         | 1;1      | 136,240.0411   | 5      | 1          |
| test_benchmark_file_handler_cm_write[100]                        | 6.1000         | 21.9001        | 9.7000         | 6.8495         | 6.5999         | 5.0750         | 1;1      | 103,092.4934   | 5      | 1          |
| test_benchmark_file_handler_cm_write[300]                        | 6.2999         | 17.3000        | 8.7200         | 4.7997         | 6.6001         | 2.8999         | 1;1      | 114,678.9445   | 5      | 1          |
| test_benchmark_file_handler_cm_write_no_flush[1000]              | 6.3999         | 16.6000        | 8.5600         | 4.4992         | 6.5000         | 2.9250         | 1;1      | 116,822.1759   | 5      | 1          |
| test_benchmark_file_handler_cm_write_no_flush[500]               | 6.3999         | 47.3000        | 16.5000        | 17.3700        | 10.1001        | 14.0500        | 1;1      | 60,606.1122    | 5      | 1          |
| test_benchmark_file_handler_cm_write_no_flush[2000]              | 6.5999         | 15.9000        | 8.5600         | 4.1089         | 6.6001         | 2.7000         | 1;1      | 116,822.8114   | 5      | 1          |
| test_benchmark_file_handler_write[100]                           | 18,077.6000    | 26,501.7999    | 21,050.4750    | 2,596.9549     | 21,012.0000    | 3,297.5500     | 6;0      | 47.5049        | 16     | 1          |
| test_benchmark_file_handler_write_no_flush[100]                  | 25,478.1999    | 46,711.0000    | 32,948.7091    | 7,068.4663     | 31,048.3000    | 12,045.4750    | 2;0      | 30.3502        | 11     | 1          |
| test_benchmark_file_handler_write[300]                           | 54,180.5000    | 74,543.7001    | 62,225.0000    | 7,471.3613     | 61,143.6000    | 5,880.4000     | 2;1      | 16.0707        | 5      | 1          |
| test_benchmark_file_handler_write_no_flush[300]                  | 77,133.9000    | 102,703.5000   | 86,339.2800    | 9,641.6473     | 83,501.4001    | 7,865.8500     | 1;1      | 11.5822        | 5      | 1          |
| test_benchmark_file_handler_write[500]                           | 94,093.9999    | 100,898.7000   | 98,507.2600    | 2,588.8400     | 99,167.1999    | 2,231.1251     | 1;1      | 10.1515        | 5      | 1          |
| test_benchmark_file_handler_write_no_flush[500]                  | 135,137.5999   | 281,826.0000   | 185,157.2400   | 65,024.5786    | 142,720.0000   | 97,196.5000    | 1;0      | 5.4008         | 5      | 1          |
| test_benchmark_file_handler_write[1000]                          | 183,361.7999   | 263,183.2000   | 216,252.8200   | 31,145.4948    | 210,634.9000   | 44,347.4500    | 2;0      | 4.6242         | 5      | 1          |
| test_benchmark_file_handler_write_no_flush[1000]                 | 243,713.3000   | 277,036.2000   | 260,464.3200   | 13,665.5138    | 256,109.4000   | 21,852.2500    | 2;0      | 3.8393         | 5      | 1          |
| test_benchmark_file_handler_write[2000]                          | 492,953.5000   | 556,571.1000   | 526,605.2200   | 23,875.5877    | 521,814.3000   | 30,559.2500    | 2;0      | 1.8990         | 5      | 1          |
| test_benchmark_file_handler_write_no_flush[2000]                 | 508,383.9000   | 597,610.7001   | 541,302.8800   | 34,377.4183    | 536,981.1000   | 39,817.0250    | 1;0      | 1.8474         | 5      | 1          |


**Asynchronous File Handling (`FileHandler_ASYNC`)**

---

## Summary

The benchmarks demonstrate the efficiency of `jr_py_writer` in both synchronous and asynchronous file handling scenarios. The library performs well across various batch sizes, with minimal overhead and consistent performance.

---

## Testing

To run the benchmarks, use the following commands:

```bash
pytest tests/
pytest tests/test_bench_sync_file_handler.py
pytest tests/test_bench_async_file_handler.py
```

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE)
