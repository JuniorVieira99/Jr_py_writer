# Performance Time Tables `jr_py_writer`

This document provides a detailed overview of the performance benchmarks for the `jr_py_writer` package, specifically focusing on the time taken for various file handling operations. The benchmarks were conducted in Linux, Windows and MacOs environments using GitHub Actions runners.

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
- Python Version: 3.13

#### Linux Environment Results

This table summarizes the performance times for various operations in the system.

| Test Name                                                       | Messages | Time Taken (s) | Context Manager | Flush | Async | Status |
|-----------------------------------------------------------------|----------|----------------|-----------------|-------|-------|--------|
| test_file_handler_log_batches[100]                             | 100      | 0.002          | No              | Yes   | No    | PASSED |
| test_file_handler_log_batches[300]                             | 300      | 0.007          | No              | Yes   | No    | PASSED |
| test_file_handler_log_batches[500]                             | 500      | 0.010          | No              | Yes   | No    | PASSED |
| test_file_handler_log_batches[1000]                            | 1000     | 0.022          | No              | Yes   | No    | PASSED |
| test_file_handler_log_batches[2000]                            | 2000     | 0.047          | No              | Yes   | No    | PASSED |
| test_file_handler_cm_log_batches[100]                          | 100      | 0.008          | Yes             | Yes   | No    | PASSED |
| test_file_handler_cm_log_batches[300]                          | 300      | 0.023          | Yes             | Yes   | No    | PASSED |
| test_file_handler_cm_log_batches[500]                          | 500      | 0.041          | Yes             | Yes   | No    | PASSED |
| test_file_handler_cm_log_batches[1000]                         | 1000     | 0.059          | Yes             | Yes   | No    | PASSED |
| test_file_handler_cm_log_batches[2000]                         | 2000     | 0.128          | Yes             | Yes   | No    | PASSED |
| test_file_handler_log_batches_no_flush[100]                    | 100      | 0.004          | No              | No    | No    | PASSED |
| test_file_handler_log_batches_no_flush[300]                    | 300      | 0.013          | No              | No    | No    | PASSED |
| test_file_handler_log_batches_no_flush[500]                    | 500      | 0.023          | No              | No    | No    | PASSED |
| test_file_handler_log_batches_no_flush[1000]                   | 1000     | 0.021          | No              | No    | No    | PASSED |
| test_file_handler_log_batches_no_flush[2000]                   | 2000     | 0.047          | No              | No    | No    | PASSED |
| test_file_handler_cm_log_batches_no_flush[100]                 | 100      | 0.007          | Yes             | No    | No    | PASSED |
| test_file_handler_cm_log_batches_no_flush[300]                 | 300      | 0.018          | Yes             | No    | No    | PASSED |
| test_file_handler_cm_log_batches_no_flush[500]                 | 500      | 0.029          | Yes             | No    | No    | PASSED |
| test_file_handler_cm_log_batches_no_flush[1000]                | 1000     | 0.052          | Yes             | No    | No    | PASSED |
| test_file_handler_cm_log_batches_no_flush[2000]                | 2000     | 0.093          | Yes             | No    | No    | PASSED |
| test_file_handler_log_async_batches[100]                       | 100      | 0.010          | No              | Yes   | Yes   | PASSED |
| test_file_handler_log_async_batches[300]                       | 300      | 0.010          | No              | Yes   | Yes   | PASSED |
| test_file_handler_log_async_batches[500]                       | 500      | 0.030          | No              | Yes   | Yes   | PASSED |
| test_file_handler_log_async_batches[1000]                      | 1000     | 0.040          | No              | Yes   | Yes   | PASSED |
| test_file_handler_log_async_batches[2000]                      | 2000     | 0.070          | No              | Yes   | Yes   | PASSED |
| test_file_handler_cm_log_async_batches[100]                    | 100      | 0.010          | Yes             | Yes   | Yes   | PASSED |
| test_file_handler_cm_log_async_batches[300]                    | 300      | 0.020          | Yes             | Yes   | Yes   | PASSED |
| test_file_handler_cm_log_async_batches[500]                    | 500      | 0.040          | Yes             | Yes   | Yes   | PASSED |
| test_file_handler_cm_log_async_batches[1000]                   | 1000     | 0.060          | Yes             | Yes   | Yes   | PASSED |
| test_file_handler_cm_log_async_batches[2000]                   | 2000     | 0.120          | Yes             | Yes   | Yes   | PASSED |
| test_file_handler_log_async_batches_no_flush[100]              | 100      | 0.000          | No              | No    | Yes   | PASSED |
| test_file_handler_log_async_batches_no_flush[300]              | 300      | 0.010          | No              | No    | Yes   | PASSED |
| test_file_handler_log_async_batches_no_flush[500]              | 500      | 0.020          | No              | No    | Yes   | PASSED |
| test_file_handler_log_async_batches_no_flush[1000]             | 1000     | 0.020          | No              | No    | Yes   | PASSED |
| test_file_handler_log_async_batches_no_flush[2000]             | 2000     | 0.040          | No              | No    | Yes   | PASSED |
| test_file_handler_cm_log_async_batches_no_flush[100]           | 100      | 0.010          | Yes             | No    | Yes   | PASSED |
| test_file_handler_cm_log_async_batches_no_flush[300]           | 300      | 0.020          | Yes             | No    | Yes   | PASSED |
| test_file_handler_cm_log_async_batches_no_flush[500]           | 500      | 0.030          | Yes             | No    | Yes   | PASSED |
| test_file_handler_cm_log_async_batches_no_flush[1000]          | 1000     | 0.040          | Yes             | No    | Yes   | PASSED |
| test_file_handler_cm_log_async_batches_no_flush[2000]          | 2000     | 0.110          | Yes             | No    | Yes   | PASSED |

### Windows Environment

- Memory (RAM): 16 GB
- Processor (CPU): AMD EPYC 7B12 processors
- Cores (CPU): 4 cores
- Storage (SSD): 14 GB
- Workflow Labels: windows-latest, windows-2025, windows-2022, windows-2019

### Windows Environment Results

| Test Name                                                       | Messages | Time Taken (s) | Context Manager | Flush | Async | Status |
|-----------------------------------------------------------------|----------|----------------|-----------------|-------|-------|--------|
| test_file_handler_log_batches[100]                             | 100      | 0.016          | No              | Yes   | No    | PASSED |
| test_file_handler_log_batches[300]                             | 300      | 0.063          | No              | Yes   | No    | PASSED |
| test_file_handler_log_batches[500]                             | 500      | 0.087          | No              | Yes   | No    | PASSED |
| test_file_handler_log_batches[1000]                            | 1000     | 0.157          | No              | Yes   | No    | PASSED |
| test_file_handler_log_batches[2000]                            | 2000     | 0.328          | No              | Yes   | No    | PASSED |
| test_file_handler_cm_log_batches[100]                          | 100      | 0.031          | Yes             | Yes   | No    | PASSED |
| test_file_handler_cm_log_batches[300]                          | 300      | 0.094          | Yes             | Yes   | No    | PASSED |
| test_file_handler_cm_log_batches[500]                          | 500      | 0.156          | Yes             | Yes   | No    | PASSED |
| test_file_handler_cm_log_batches[1000]                         | 1000     | 0.266          | Yes             | Yes   | No    | PASSED |
| test_file_handler_cm_log_batches[2000]                         | 2000     | 0.563          | Yes             | Yes   | No    | PASSED |
| test_file_handler_log_batches_no_flush[100]                    | 100      | 0.016          | No              | No    | No    | PASSED |
| test_file_handler_log_batches_no_flush[300]                    | 300      | 0.031          | No              | No    | No    | PASSED |
| test_file_handler_log_batches_no_flush[500]                    | 500      | 0.063          | No              | No    | No    | PASSED |
| test_file_handler_log_batches_no_flush[1000]                   | 1000     | 0.109          | No              | No    | No    | PASSED |
| test_file_handler_log_batches_no_flush[2000]                   | 2000     | 0.141          | No              | No    | No    | PASSED |
| test_file_handler_cm_log_batches_no_flush[100]                 | 100      | 0.016          | Yes             | No    | No    | PASSED |
| test_file_handler_cm_log_batches_no_flush[300]                 | 300      | 0.078          | Yes             | No    | No    | PASSED |
| test_file_handler_cm_log_batches_no_flush[500]                 | 500      | 0.141          | Yes             | No    | No    | PASSED |
| test_file_handler_cm_log_batches_no_flush[1000]                | 1000     | 0.250          | Yes             | No    | No    | PASSED |
| test_file_handler_cm_log_batches_no_flush[2000]                | 2000     | 0.521          | Yes             | No    | No    | PASSED |
| test_file_handler_log_async_batches[100]                       | 100      | 0.020          | No              | Yes   | Yes   | PASSED |
| test_file_handler_log_async_batches[300]                       | 300      | 0.030          | No              | Yes   | Yes   | PASSED |
| test_file_handler_log_async_batches[500]                       | 500      | 0.060          | No              | Yes   | Yes   | PASSED |
| test_file_handler_log_async_batches[1000]                      | 1000     | 0.080          | No              | Yes   | Yes   | PASSED |
| test_file_handler_log_async_batches[2000]                      | 2000     | 0.170          | No              | Yes   | Yes   | PASSED |
| test_file_handler_cm_log_async_batches[100]                    | 100      | 0.020          | Yes             | Yes   | Yes   | PASSED |
| test_file_handler_cm_log_async_batches[300]                    | 300      | 0.080          | Yes             | Yes   | Yes   | PASSED |
| test_file_handler_cm_log_async_batches[500]                    | 500      | 0.130          | Yes             | Yes   | Yes   | PASSED |
| test_file_handler_cm_log_async_batches[1000]                   | 1000     | 0.250          | Yes             | Yes   | Yes   | PASSED |
| test_file_handler_cm_log_async_batches[2000]                   | 2000     | 0.480          | Yes             | Yes   | Yes   | PASSED |
| test_file_handler_log_async_batches_no_flush[100]              | 100      | 0.020          | No              | No    | Yes   | PASSED |
| test_file_handler_log_async_batches_no_flush[300]              | 300      | 0.030          | No              | No    | Yes   | PASSED |
| test_file_handler_log_async_batches_no_flush[500]              | 500      | 0.050          | No              | No    | Yes   | PASSED |
| test_file_handler_log_async_batches_no_flush[1000]             | 1000     | 0.060          | No              | No    | Yes   | PASSED |
| test_file_handler_log_async_batches_no_flush[2000]             | 2000     | 0.140          | No              | No    | Yes   | PASSED |
| test_file_handler_cm_log_async_batches_no_flush[100]           | 100      | 0.020          | Yes             | No    | Yes   | PASSED |
| test_file_handler_cm_log_async_batches_no_flush[300]           | 300      | 0.060          | Yes             | No    | Yes   | PASSED |
| test_file_handler_cm_log_async_batches_no_flush[500]           | 500      | 0.120          | Yes             | No    | Yes   | PASSED |
| test_file_handler_cm_log_async_batches_no_flush[1000]          | 1000     | 0.220          | Yes             | No    | Yes   | PASSED |
| test_file_handler_cm_log_async_batches_no_flush[2000]          | 2000     | 0.450          | Yes             | No    | Yes   | PASSED |

### MacOS Environment

- Memory (RAM): 7 GB
- Processor (CPU): Intel Xeon W processors.
- Cores (CPU): 3 cores
- Storage (SSD): 14 GB
- Workflow Labels: macos-latest, macos-14, macos-15

### MacOS Environment Results

| Test Name                                                       | Messages | Time Taken (s) | Context Manager | Flush | Async | Status |
|-----------------------------------------------------------------|----------|----------------|-----------------|-------|-------|--------|
| test_file_handler_log_batches[100]                             | 100      | 0.002          | No              | Yes   | No    | PASSED |
| test_file_handler_log_batches[300]                             | 300      | 0.005          | No              | Yes   | No    | PASSED |
| test_file_handler_log_batches[500]                             | 500      | 0.010          | No              | Yes   | No    | PASSED |
| test_file_handler_log_batches[1000]                            | 1000     | 0.019          | No              | Yes   | No    | PASSED |
| test_file_handler_log_batches[2000]                            | 2000     | 0.039          | No              | Yes   | No    | PASSED |
| test_file_handler_cm_log_batches[100]                          | 100      | 0.007          | Yes             | Yes   | No    | PASSED |
| test_file_handler_cm_log_batches[300]                          | 300      | 0.036          | Yes             | Yes   | No    | PASSED |
| test_file_handler_cm_log_batches[500]                          | 500      | 0.065          | Yes             | Yes   | No    | PASSED |
| test_file_handler_cm_log_batches[1000]                         | 1000     | 0.066          | Yes             | Yes   | No    | PASSED |
| test_file_handler_cm_log_batches[2000]                         | 2000     | 0.136          | Yes             | Yes   | No    | PASSED |
| test_file_handler_log_batches_no_flush[100]                    | 100      | 0.004          | No              | No    | No    | PASSED |
| test_file_handler_log_batches_no_flush[300]                    | 300      | 0.012          | No              | No    | No    | PASSED |
| test_file_handler_log_batches_no_flush[500]                    | 500      | 0.239          | No              | No    | No    | PASSED |
| test_file_handler_log_batches_no_flush[1000]                   | 1000     | 0.025          | No              | No    | No    | PASSED |
| test_file_handler_log_batches_no_flush[2000]                   | 2000     | 0.054          | No              | No    | No    | PASSED |
| test_file_handler_cm_log_batches_no_flush[100]                 | 100      | 0.010          | Yes             | No    | No    | PASSED |
| test_file_handler_cm_log_batches_no_flush[300]                 | 300      | 0.069          | Yes             | No    | No    | PASSED |
| test_file_handler_cm_log_batches_no_flush[500]                 | 500      | 0.039          | Yes             | No    | No    | PASSED |
| test_file_handler_cm_log_batches_no_flush[1000]                | 1000     | 0.072          | Yes             | No    | No    | PASSED |
| test_file_handler_cm_log_batches_no_flush[2000]                | 2000     | 0.163          | Yes             | No    | No    | PASSED |
| test_file_handler_log_async_batches[100]                       | 100      | 0.010          | No              | Yes   | Yes   | PASSED |
| test_file_handler_log_async_batches[300]                       | 300      | 0.030          | No              | Yes   | Yes   | PASSED |
| test_file_handler_log_async_batches[500]                       | 500      | 0.030          | No              | Yes   | Yes   | PASSED |
| test_file_handler_log_async_batches[1000]                      | 1000     | 0.040          | No              | Yes   | Yes   | PASSED |
| test_file_handler_log_async_batches[2000]                      | 2000     | 0.100          | No              | Yes   | Yes   | PASSED |
| test_file_handler_cm_log_async_batches[100]                    | 100      | 0.010          | Yes             | Yes   | Yes   | PASSED |
| test_file_handler_cm_log_async_batches[300]                    | 300      | 0.030          | Yes             | Yes   | Yes   | PASSED |
| test_file_handler_cm_log_async_batches[500]                    | 500      | 0.050          | Yes             | Yes   | Yes   | PASSED |
| test_file_handler_cm_log_async_batches[1000]                   | 1000     | 0.060          | Yes             | Yes   | Yes   | PASSED |
| test_file_handler_cm_log_async_batches[2000]                   | 2000     | 0.130          | Yes             | Yes   | Yes   | PASSED |
| test_file_handler_log_async_batches_no_flush[100]              | 100      | 0.010          | No              | No    | Yes   | PASSED |
| test_file_handler_log_async_batches_no_flush[300]              | 300      | 0.040          | No              | No    | Yes   | PASSED |
| test_file_handler_log_async_batches_no_flush[500]              | 500      | 0.020          | No              | No    | Yes   | PASSED |
| test_file_handler_log_async_batches_no_flush[1000]             | 1000     | 0.030          | No              | No    | Yes   | PASSED |
| test_file_handler_log_async_batches_no_flush[2000]             | 2000     | 0.080          | No              | No    | Yes   | PASSED |
| test_file_handler_cm_log_async_batches_no_flush[100]           | 100      | 0.010          | Yes             | No    | Yes   | PASSED |
| test_file_handler_cm_log_async_batches_no_flush[300]           | 300      | 0.030          | Yes             | No    | Yes   | PASSED |
| test_file_handler_cm_log_async_batches_no_flush[500]           | 500      | 0.030          | Yes             | No    | Yes   | PASSED |
| test_file_handler_cm_log_async_batches_no_flush[1000]          | 1000     | 0.080          | Yes             | No    | Yes   | PASSED |
| test_file_handler_cm_log_async_batches_no_flush[2000]          | 2000     | 0.120          | Yes             | No    | Yes   | PASSED |