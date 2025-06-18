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
- Python Version: 3.13

#### Linux Environment Results

**Synchronous File Handling (`FileHandler_SYNC`)**

| Name                                                              | Min (ns)         | Max (ns)         | Mean (ns)        | StdDev (ns)      | Median (ns)      | IQR (ns)        | Outliers | OPS         | Rounds | Iterations |
|-------------------------------------------------------------------|------------------|------------------|------------------|------------------|------------------|----------------|----------|-------------|--------|------------|
| test_benchmark_file_handler_cm_write[300]                        | 841.0000         | 4,318.0000       | 1,108.6341       | 534.1470         | 992.0000         | 160.0000       | 2;2      | 902,010.8224 | 41     | 1          |
| test_benchmark_file_handler_cm_write_no_flush[100]               | 872.0000         | 5,060.0000       | 1,026.4786       | 388.8130         | 981.0000         | 70.0000        | 2;9      | 974,204.3986 | 117    | 1          |
| test_benchmark_file_handler_cm_write_no_flush[300]               | 881.0000         | 4,488.0000       | 1,124.3250       | 572.0442         | 996.5000         | 140.0000       | 2;3      | 889,422.5435 | 40     | 1          |
| test_benchmark_file_handler_cm_write[100]                        | 892.0000         | 6,312.0000       | 1,071.6038       | 538.2265         | 992.0000         | 90.0000        | 3;6      | 933,180.7376 | 106    | 1          |
| test_benchmark_file_handler_cm_write_no_flush[500]               | 892.0000         | 4,758.0000       | 1,255.5600       | 755.2683         | 1,062.0000       | 247.5000       | 1;2      | 796,457.3588 | 25     | 1          |
| test_benchmark_file_handler_cm_write[1000]                       | 901.0000         | 4,579.0000       | 1,298.5000       | 891.6389         | 1,012.0000       | 255.5000       | 1;1      | 770,119.3690 | 16     | 1          |
| test_benchmark_file_handler_cm_write[500]                        | 912.0000         | 4,278.0000       | 1,198.4167       | 671.7637         | 1,032.0000       | 135.5000       | 1;2      | 834,434.3214 | 24     | 1          |
| test_benchmark_file_handler_cm_write[2000]                       | 982.0000         | 6,291.0000       | 1,759.5000       | 1,840.1185       | 1,052.0000       | 335.5000       | 1;1      | 568,343.2788 | 8      | 1          |
| test_benchmark_file_handler_cm_write_no_flush[2000]              | 1,072.0000       | 6,803.0000       | 2,110.8571       | 2,079.5958       | 1,392.0000       | 460.7500       | 1;1      | 473,741.2028 | 7      | 1          |
| test_benchmark_file_handler_cm_write_no_flush[1000]              | 1,132.0000       | 6,011.0000       | 1,695.0714       | 1,263.1723       | 1,327.5000       | 291.0000       | 1;2      | 589,945.6429 | 14     | 1          |
| test_benchmark_file_handler_write_no_flush[100]                  | 4,947,600.0000   | 5,592,308.0000   | 5,243,519.9194   | 122,080.1063     | 5,227,240.0000   | 179,617.0000   | 37;0     | 190.7116     | 124    | 1          |
| test_benchmark_file_handler_write[100]                           | 5,621,894.0000   | 7,702,898.0000   | 6,556,516.9515   | 365,347.2802     | 6,525,753.0000   | 585,166.5000   | 35;0     | 152.5200     | 103    | 1          |
| test_benchmark_file_handler_write_no_flush[300]                  | 15,418,381.0000  | 24,974,771.0000  | 16,007,417.0233  | 1,416,701.5720   | 15,743,273.0000  | 322,684.0000   | 1;1      | 62.4710      | 43     | 1          |
| test_benchmark_file_handler_write[300]                           | 18,114,116.0000  | 29,440,416.0000  | 19,451,620.8372  | 1,787,939.9901   | 19,005,637.0000  | 777,101.2500   | 4;4      | 51.4096      | 43     | 1          |
| test_benchmark_file_handler_write_no_flush[500]                  | 26,037,232.0000  | 27,559,616.0000  | 26,567,905.5385  | 355,160.5708     | 26,535,183.5000  | 429,208.0000   | 6;1      | 37.6394      | 26     | 1          |
| test_benchmark_file_handler_write[500]                           | 30,465,635.0000  | 32,813,185.0000  | 31,816,645.9600  | 624,181.8248     | 31,852,727.0000  | 834,776.7500   | 8;0      | 31.4301      | 25     | 1          |
| test_benchmark_file_handler_write_no_flush[1000]                 | 41,405,766.0000  | 43,432,096.0000  | 42,291,873.2000  | 605,748.3699     | 42,158,270.0000  | 642,146.0000   | 5;0      | 23.6452      | 15     | 1          |
| test_benchmark_file_handler_write[1000]                          | 42,876,370.0000  | 47,837,374.0000  | 46,349,906.1333  | 1,123,430.5027   | 46,695,083.0000  | 531,809.0000   | 3;3      | 21.5750      | 15     | 1          |
| test_benchmark_file_handler_write_no_flush[2000]                 | 81,284,955.0000  | 85,370,648.0000  | 83,570,465.4286  | 1,621,561.6287   | 84,359,398.0000  | 2,720,211.2500 | 2;0      | 11.9659      | 7      | 1          |
| test_benchmark_file_handler_write[2000]                          | 89,500,582.0000  | 95,450,655.0000  | 93,148,808.6250  | 2,017,109.1054   | 93,380,473.0000  | 2,856,264.0000 | 2;0      | 10.7355      | 8      | 1          |

**Asynchronous File Handling (`FileHandler_ASYNC`)**

| Name                                                              | Min (us) | Max (us) | Mean (us) | StdDev (us) | Median (us) | IQR (us) | Outliers   | OPS (Kops/s) | Rounds | Iterations |
|-------------------------------------------------------------------|----------|----------|-----------|-------------|-------------|----------|------------|--------------|--------|------------|
| test_benchmark_async_file_handler_write_no_flush[1000]           | 1.4030   | 39.3610  | 1.4985    | 0.4064      | 1.4730      | 0.0300   | 333;1548   | 667.3500     | 72276  | 1          |
| test_benchmark_async_file_handler_write[100]                     | 1.4120   | 36.5260  | 1.4884    | 0.4354      | 1.4630      | 0.0290   | 158;729    | 671.8499     | 32909  | 1          |
| test_benchmark_async_file_handler_write[500]                     | 1.4120   | 23.6240  | 1.4860    | 0.3682      | 1.4630      | 0.0290   | 268;1212   | 672.9416     | 64730  | 1          |
| test_benchmark_async_file_handler_write_no_flush[300]            | 1.4130   | 55.0950  | 1.5066    | 0.4833      | 1.4830      | 0.0290   | 332;1696   | 663.7497     | 83112  | 1          |
| test_benchmark_async_file_handler_write[1000]                    | 1.4130   | 23.3630  | 1.5293    | 0.4728      | 1.4820      | 0.0300   | 1403;2369  | 653.8987     | 58645  | 1          |
| test_benchmark_async_cm_file_handler_write[1000]                 | 1.4220   | 23.4540  | 1.5038    | 0.3736      | 1.4830      | 0.0290   | 288;1179   | 664.9859     | 61653  | 1          |
| test_benchmark_async_cm_file_handler_write_no_flush[1000]        | 1.4220   | 18.7450  | 1.5038    | 0.3912      | 1.4830      | 0.0210   | 393;2490   | 664.9803     | 70191  | 1          |
| test_benchmark_async_cm_file_handler_write_no_flush[2000]        | 1.4220   | 16.3110  | 1.5078    | 0.3568      | 1.4830      | 0.0290   | 278;853    | 663.2083     | 46124  | 1          |
| test_benchmark_async_cm_file_handler_write_no_flush[300]         | 1.4220   | 29.6350  | 1.5001    | 0.3569      | 1.4830      | 0.0210   | 386;3443   | 666.6330     | 86423  | 1          |
| test_benchmark_async_file_handler_write[300]                     | 1.4220   | 26.3790  | 1.5033    | 0.3815      | 1.4830      | 0.0200   | 406;3387   | 665.1843     | 83809  | 1          |
| test_benchmark_async_file_handler_write_no_flush[100]            | 1.4230   | 24.4760  | 1.5079    | 0.3809      | 1.4830      | 0.0200   | 516;2316   | 663.1942     | 65109  | 1          |
| test_benchmark_async_cm_file_handler_write[2000]                 | 1.4320   | 18.0130  | 1.5053    | 0.3519      | 1.4830      | 0.0290   | 227;1042   | 664.3315     | 55482  | 1          |
| test_benchmark_async_cm_file_handler_write[500]                  | 1.4320   | 42.7800  | 1.5134    | 0.3937      | 1.4930      | 0.0200   | 331;3381   | 660.7801     | 78784  | 1          |
| test_benchmark_async_cm_file_handler_write_no_flush[100]         | 1.4320   | 28.7230  | 1.5102    | 0.4064      | 1.4830      | 0.0290   | 440;1157   | 662.1509     | 62858  | 1          |
| test_benchmark_async_cm_file_handler_write_no_flush[500]         | 1.4320   | 17.6930  | 1.5129    | 0.3768      | 1.4930      | 0.0210   | 387;2992   | 660.9999     | 79663  | 1          |
| test_benchmark_async_cm_file_handler_write[300]                  | 1.4320   | 18.3540  | 1.5172    | 0.3604      | 1.4930      | 0.0290   | 429;1632   | 659.1072     | 80045  | 1          |
| test_benchmark_async_cm_file_handler_write[100]                  | 1.4420   | 27.6510  | 1.5290    | 0.4354      | 1.4930      | 0.0290   | 832;1368   | 654.0051     | 65669  | 1          |
| test_benchmark_async_file_handler_write_no_flush[2000]           | 1.4420   | 19.6860  | 1.5179    | 0.3498      | 1.4930      | 0.0300   | 283;965    | 658.8052     | 51029  | 1          |
| test_benchmark_async_file_handler_write_no_flush[500]            | 1.4420   | 26.1290  | 1.5243    | 0.3964      | 1.5030      | 0.0210   | 389;2942   | 656.0582     | 76366  | 1          |
| test_benchmark_async_file_handler_write[2000]                    | 1.4420   | 29.0340  | 1.5251    | 0.3744      | 1.5030      | 0.0300   | 197;1017   | 655.6749     | 50901  | 1          |

#### Windows Environment

- Memory (RAM): 16 GB
- Processor (CPU): AMD EPYC 7B12 processors
- Cores (CPU): 4 cores
- Storage (SSD): 14 GB
- Workflow Labels: windows-latest, windows-2025, windows-2022, windows-2019

#### Windows Environment Results

**Synchronous File Handling (`FileHandler_SYNC`)**

| Name                                                              | Min (us)         | Max (us)         | Mean (us)        | StdDev (us)      | Median (us)      | IQR (us)        | Outliers | OPS         | Rounds | Iterations |
|-------------------------------------------------------------------|------------------|------------------|------------------|------------------|------------------|----------------|----------|-------------|--------|------------|
| test_benchmark_file_handler_cm_write_no_flush[100]               | 1.5000           | 10.4000          | 1.8774           | 1.6022           | 1.5000           | 0.1000         | 1;4      | 532,646.0480 | 31     | 1          |
| test_benchmark_file_handler_cm_write[100]                        | 1.5000           | 7.8000           | 1.8800           | 1.1409           | 1.6000           | 0.1000         | 1;3      | 531,914.8877 | 30     | 1          |
| test_benchmark_file_handler_cm_write[2000]                       | 1.7000           | 13.8000          | 4.3800           | 5.2808           | 1.9000           | 3.7000         | 1;1      | 228,310.5013 | 5      | 1          |
| test_benchmark_file_handler_cm_write[300]                        | 1.7000           | 11.1000          | 2.8900           | 2.8973           | 1.9000           | 0.1000         | 1;3      | 346,020.7617 | 10     | 1          |
| test_benchmark_file_handler_cm_write_no_flush[1000]              | 1.7000           | 13.1000          | 4.1800           | 4.9972           | 1.9000           | 3.4500         | 1;1      | 239,234.4474 | 5      | 1          |
| test_benchmark_file_handler_cm_write_no_flush[500]               | 1.7000           | 12.3000          | 3.4857           | 3.9045           | 1.9000           | 0.8250         | 1;1      | 286,885.2456 | 7      | 1          |
| test_benchmark_file_handler_cm_write[1000]                       | 1.8000           | 11.8000          | 4.0000           | 4.3766           | 1.9000           | 3.1750         | 1;1      | 249,999.9949 | 5      | 1          |
| test_benchmark_file_handler_cm_write_no_flush[300]               | 2.0000           | 10.6000          | 3.0000           | 2.5472           | 2.1000           | 0.2250         | 1;2      | 333,333.3422 | 11     | 1          |
| test_benchmark_file_handler_cm_write_no_flush[2000]              | 2.3000           | 16.0000          | 5.3200           | 5.9956           | 2.4000           | 4.4000         | 1;1      | 187,969.9251 | 5      | 1          |
| test_benchmark_file_handler_cm_write[500]                        | 2.6000           | 9.4000           | 4.1000           | 2.6668           | 2.9000           | 1.6000         | 1;1      | 243,902.4372 | 6      | 1          |
| test_benchmark_file_handler_write_no_flush[100]                  | 8,867.1000       | 22,004.1000      | 10,101.7853      | 2,152.0610       | 9,843.2000       | 814.8000       | 1;1      | 98.9924      | 34     | 1          |
| test_benchmark_file_handler_write[100]                           | 11,042.6000      | 20,456.2000      | 12,155.1000      | 1,598.9724       | 11,703.2500      | 661.2000       | 1;1      | 82.2700      | 32     | 1          |
| test_benchmark_file_handler_write_no_flush[300]                  | 29,063.0000      | 32,216.4000      | 30,540.8250      | 981.0165         | 30,293.7500      | 1,441.7000     | 5;0      | 32.7431      | 12     | 1          |
| test_benchmark_file_handler_write[300]                           | 35,953.3000      | 40,960.9000      | 37,336.6727      | 1,297.5526       | 37,183.1000      | 680.4250       | 2;1      | 26.7833      | 11     | 1          |
| test_benchmark_file_handler_write_no_flush[500]                  | 49,135.6000      | 58,158.6000      | 52,680.9857      | 2,900.4950       | 52,032.1000      | 2,784.8000     | 2;1      | 18.9822      | 7      | 1          |
| test_benchmark_file_handler_write[500]                           | 61,893.0000      | 79,990.4000      | 65,338.6571      | 6,554.2393       | 63,012.1000      | 2,555.5250     | 1;1      | 15.3049      | 7      | 1          |
| test_benchmark_file_handler_write_no_flush[1000]                 | 84,631.6000      | 95,829.9000      | 87,719.5000      | 4,612.8577       | 86,282.8000      | 4,012.1750     | 1;1      | 11.4000      | 5      | 1          |
| test_benchmark_file_handler_write[1000]                          | 96,985.0000      | 106,901.0000     | 100,107.6200     | 3,954.3955       | 99,205.4000      | 3,979.6750     | 1;0      | 9.9892       | 5      | 1          |
| test_benchmark_file_handler_write_no_flush[2000]                 | 169,651.6000     | 220,630.8000     | 183,485.1600     | 20,957.4949      | 176,537.3000     | 14,738.6750    | 1;1      | 5.4500       | 5      | 1          |
| test_benchmark_file_handler_write[2000]                          | 192,619.8000     | 211,032.4000     | 200,035.6000     | 6,918.7975       | 199,200.2000     | 8,135.0500     | 2;0      | 4.9991       | 5      | 1          |

**Asynchronous File Handling (`FileHandler_ASYNC`)**

| Name                                                              | Min (us) | Max (us)   | Mean (us) | StdDev (us) | Median (us) | IQR (us) | Outliers     | OPS (Kops/s) | Rounds  | Iterations |
|-------------------------------------------------------------------|----------|------------|-----------|-------------|-------------|----------|--------------|--------------|---------|------------|
| test_benchmark_async_cm_file_handler_write[1000]                 | 1.5000   | 24.3000    | 1.6145    | 0.2302      | 1.6000      | 0.0000   | 242;7916     | 619.3704     | 39841   | 1          |
| test_benchmark_async_cm_file_handler_write[100]                  | 1.5000   | 45.7000    | 1.6086    | 0.3911      | 1.6000      | 0.0000   | 104;7297     | 621.6696     | 44053   | 1          |
| test_benchmark_async_cm_file_handler_write[2000]                 | 1.5000   | 28.1000    | 1.6158    | 0.2818      | 1.6000      | 0.0000   | 276;6505     | 618.8709     | 37038   | 1          |
| test_benchmark_async_cm_file_handler_write[300]                  | 1.5000   | 59.2000    | 1.6043    | 0.4370      | 1.6000      | 0.0000   | 187;9570     | 623.3316     | 43479   | 1          |
| test_benchmark_async_cm_file_handler_write[500]                  | 1.5000   | 36.5000    | 1.6160    | 0.2944      | 1.6000      | 0.0000   | 381;7318     | 618.8235     | 38911   | 1          |
| test_benchmark_async_cm_file_handler_write_no_flush[1000]        | 1.5000   | 67.1000    | 1.6263    | 0.6522      | 1.6000      | 0.0000   | 141;7044     | 614.8768     | 37594   | 1          |
| test_benchmark_async_cm_file_handler_write_no_flush[100]         | 1.5000   | 3,935.1000 | 1.7076    | 19.4008     | 1.6000      | 0.0000   | 7;8557       | 585.6303     | 41153   | 1          |
| test_benchmark_async_cm_file_handler_write_no_flush[2000]        | 1.5000   | 78.7000    | 1.6297    | 0.6467      | 1.6000      | 0.0000   | 129;9035     | 613.6210     | 38611   | 1          |
| test_benchmark_async_cm_file_handler_write_no_flush[300]         | 1.5000   | 52.4000    | 1.6150    | 0.4485      | 1.6000      | 0.0000   | 183;7237     | 619.1818     | 40161   | 1          |
| test_benchmark_async_cm_file_handler_write_no_flush[500]         | 1.5000   | 91.0000    | 1.6508    | 0.7913      | 1.6000      | 0.0000   | 525;8291     | 605.7623     | 40984   | 1          |
| test_benchmark_async_file_handler_write[1000]                    | 1.5000   | 17.6000    | 1.5971    | 0.1438      | 1.6000      | 0.0000   | 149;8820     | 626.1299     | 38168   | 1          |
| test_benchmark_async_file_handler_write[100]                     | 1.5000   | 28.7000    | 1.6130    | 0.2267      | 1.6000      | 0.0000   | 71;4537      | 619.9813     | 24753   | 1          |
| test_benchmark_async_file_handler_write[2000]                    | 1.5000   | 29.6000    | 1.6447    | 0.2668      | 1.6000      | 0.1000   | 91;100       | 608.0170     | 38462   | 1          |
| test_benchmark_async_file_handler_write[300]                     | 1.5000   | 43.2000    | 1.6100    | 0.3714      | 1.6000      | 0.0000   | 166;7908     | 621.1007     | 41842   | 1          |
| test_benchmark_async_file_handler_write[500]                     | 1.5000   | 34.1000    | 1.6279    | 0.2776      | 1.6000      | 0.0000   | 95;10631     | 614.2814     | 40486   | 1          |
| test_benchmark_async_file_handler_write_no_flush[1000]           | 1.5000   | 53.8000    | 1.5958    | 0.4279      | 1.6000      | 0.0000   | 184;10257    | 626.6622     | 41494   | 1          |
| test_benchmark_async_file_handler_write_no_flush[100]            | 1.5000   | 59.2000    | 1.6096    | 0.4551      | 1.6000      | 0.0000   | 189;7629     | 621.2765     | 44643   | 1          |
| test_benchmark_async_file_handler_write_no_flush[2000]           | 1.5000   | 3,733.7000 | 1.7150    | 19.7171     | 1.6000      | 0.0000   | 4;6858       | 583.0804     | 35843   | 1          |
| test_benchmark_async_file_handler_write_no_flush[300]            | 1.5000   | 71.0000    | 1.6442    | 0.6697      | 1.6000      | 0.1000   | 349;387      | 608.1964     | 41153   | 1          |
| test_benchmark_async_file_handler_write_no_flush[500]            | 1.5000   | 97.5000    | 1.6145    | 0.5535      | 1.6000      | 0.0000   | 206;8773     | 619.3884     | 41667   | 1          |

#### MacOS Environment

- Memory (RAM): 7 GB
- Processor (CPU): Intel Xeon W processors.
- Cores (CPU): 3 cores
- Storage (SSD): 14 GB
- Workflow Labels: macos-latest, macos-14, macos-15

#### MacOS Environment Results

**Synchronous File Handling (`FileHandler_SYNC`)**

| Name                                                              | Min (ns)         | Max (ns)         | Mean (ns)        | StdDev (ns)      | Median (ns)      | IQR (ns)        | Outliers | OPS         | Rounds | Iterations |
|-------------------------------------------------------------------|------------------|------------------|------------------|------------------|------------------|----------------|----------|-------------|--------|------------|
| test_benchmark_file_handler_cm_write[300]                        | 583.0000         | 12,375.0000      | 1,896.8095       | 2,506.5783       | 1,500.0000       | 1,312.2500     | 1;1      | 527,201.0642 | 21     | 1          |
| test_benchmark_file_handler_cm_write[500]                        | 583.0000         | 7,666.0000       | 1,379.0000       | 2,211.0279       | 666.5000         | 125.0000       | 1;1      | 725,163.1544 | 10     | 1          |
| test_benchmark_file_handler_cm_write_no_flush[1000]              | 583.0000         | 6,667.0000       | 1,036.0000       | 1,560.7231       | 625.0000         | 42.0000        | 1;3      | 965,250.9622 | 15     | 1          |
| test_benchmark_file_handler_cm_write_no_flush[2000]              | 583.0000         | 7,209.0000       | 2,033.4000       | 2,897.5088       | 709.0000         | 1,907.0001     | 1;1      | 491,787.1559 | 5      | 1          |
| test_benchmark_file_handler_cm_write_no_flush[500]               | 583.0000         | 6,500.0000       | 918.6500         | 1,316.4333       | 584.0000         | 62.4999        | 1;2      | 1,088,553.8602 | 20     | 1          |
| test_benchmark_file_handler_cm_write[2000]                       | 583.0000         | 26,375.0000      | 5,916.6000       | 11,439.1476      | 750.0000         | 6,853.7500     | 1;1      | 169,015.9888 | 5      | 1          |
| test_benchmark_file_handler_cm_write[1000]                       | 625.0000         | 16,792.0000      | 3,893.0000       | 5,770.8109       | 2,000.0000       | 2,229.0000     | 1;1      | 256,871.3074 | 7      | 1          |
| test_benchmark_file_handler_cm_write[100]                        | 1,625.0000       | 17,500.0000      | 1,866.4815       | 1,521.4155       | 1,708.0000       | 1.0000         | 1;45     | 535,767.4384 | 108    | 1          |
| test_benchmark_file_handler_cm_write_no_flush[300]               | 1,708.0000       | 16,375.0000      | 2,473.9167       | 2,966.0508       | 1,813.0000       | 125.5000       | 1;3      | 404,217.3343 | 24     | 1          |
| test_benchmark_file_handler_cm_write_no_flush[100]               | 1,709.0000       | 34,250.0000      | 2,424.2169       | 3,884.3000       | 1,792.0000       | 84.0000        | 2;8      | 412,504.3480 | 83     | 1          |
| test_benchmark_file_handler_write_no_flush[100]                  | 1,107,333.0000   | 12,825,125.0000  | 2,537,759.6570   | 853,505.5446     | 2,507,958.0000   | 230,312.0000   | 9;18     | 394.0483     | 172    | 1          |
| test_benchmark_file_handler_write[100]                           | 1,205,917.0000   | 22,331,291.0000  | 3,876,245.1111   | 2,806,892.2754   | 3,056,020.5000   | 1,460,875.0000 | 11;12    | 257.9816     | 162    | 1          |
| test_benchmark_file_handler_write_no_flush[300]                  | 4,225,125.0000   | 16,592,833.0000  | 8,298,679.5690   | 1,820,372.0312   | 7,961,687.5000   | 1,137,125.0000 | 9;7      | 120.5011     | 58     | 1          |
| test_benchmark_file_handler_write[300]                           | 7,770,458.0000   | 16,175,125.0000  | 9,476,665.2500   | 1,086,960.0389   | 9,338,583.5000   | 655,688.0000   | 6;4      | 105.5224     | 56     | 1          |
| test_benchmark_file_handler_write_no_flush[500]                  | 12,545,750.0000  | 20,068,625.0000  | 13,889,713.3529  | 1,599,435.9141   | 13,374,687.5000  | 551,208.0000   | 2;6      | 71.9957      | 34     | 1          |
| test_benchmark_file_handler_write[500]                           | 14,893,500.0000  | 22,746,667.0000  | 15,839,685.4516  | 1,617,786.1337   | 15,369,083.0000  | 629,396.0000   | 2;3      | 63.1326      | 31     | 1          |
| test_benchmark_file_handler_write_no_flush[1000]                 | 16,868,333.0000  | 32,280,209.0000  | 20,127,793.5000  | 3,856,165.3905   | 18,987,770.5000  | 2,670,625.0000 | 2;2      | 49.6825      | 22     | 1          |
| test_benchmark_file_handler_write[1000]                          | 20,322,750.0000  | 26,706,167.0000  | 21,700,849.1429  | 1,326,596.7137   | 21,386,959.0000  | 663,301.5000   | 3;2      | 46.0811      | 21     | 1          |
| test_benchmark_file_handler_write_no_flush[2000]                 | 36,228,708.0000  | 76,507,250.0000  | 52,208,324.0000  | 11,990,423.7640  | 53,904,083.0000  | 13,562,667.2500 | 3;0      | 19.1540      | 9      | 1          |
| test_benchmark_file_handler_write[2000]                          | 41,063,667.0000  | 47,632,209.0000  | 43,734,896.0000  | 2,287,668.2065   | 43,137,896.0000  | 3,289,083.0000 | 4;0      | 22.8650      | 8      | 1          |

**Asynchronous File Handling (`FileHandler_ASYNC`)**

| Name                                                              | Min (ns) | Max (ns)   | Mean (ns) | StdDev (ns) | Median (ns) | IQR (ns) | Outliers     | OPS (Mops/s) | Rounds  | Iterations |
|-------------------------------------------------------------------|----------|------------|-----------|-------------|-------------|----------|--------------|--------------|---------|------------|
| test_benchmark_async_cm_file_handler_write_no_flush[100]         | 708.0000 | 24,458.0000 | 851.4325  | 136.8284    | 834.0000    | 42.0000  | 104;277      | 1.1745       | 111112  | 1          |
| test_benchmark_async_cm_file_handler_write[2000]                 | 708.0000 | 13,541.0000 | 850.4697  | 129.4763    | 834.0000    | 42.0000  | 58;184       | 1.1758       | 69162   | 1          |
| test_benchmark_async_cm_file_handler_write[300]                  | 709.0000 | 36,667.0000 | 856.2193  | 205.9806    | 834.0000    | 42.0000  | 74;673       | 1.1679       | 93756   | 1          |
| test_benchmark_async_file_handler_write[1000]                    | 709.0000 | 45,708.0000 | 864.5222  | 299.1059    | 834.0000    | 42.0000  | 84;1583      | 1.1567       | 68966   | 1          |
| test_benchmark_async_cm_file_handler_write[1000]                 | 750.0000 | 75,083.0000 | 862.6669  | 372.6573    | 834.0000    | 42.0000  | 54;831       | 1.1592       | 64173   | 1          |
| test_benchmark_async_cm_file_handler_write[100]                  | 750.0000 | 28,541.0000 | 847.6609  | 180.2279    | 834.0000    | 42.0000  | 74;224       | 1.1797       | 105264  | 1          |
| test_benchmark_async_cm_file_handler_write[500]                  | 750.0000 | 42,792.0000 | 860.0267  | 269.6995    | 834.0000    | 42.0000  | 143;1665     | 1.1628       | 65394   | 1          |
| test_benchmark_async_cm_file_handler_write_no_flush[1000]        | 750.0000 | 28,208.0000 | 851.7374  | 184.4576    | 834.0000    | 42.0000  | 37;117       | 1.1741       | 66300   | 1          |
| test_benchmark_async_cm_file_handler_write_no_flush[2000]        | 750.0000 | 31,708.0000 | 863.6773  | 337.9515    | 875.0000    | 42.0000  | 45;386       | 1.1578       | 74533   | 1          |
| test_benchmark_async_cm_file_handler_write_no_flush[300]         | 750.0000 | 52,291.0000 | 854.3651  | 227.1475    | 834.0000    | 42.0000  | 48;317       | 1.1705       | 94859   | 1          |
| test_benchmark_async_cm_file_handler_write_no_flush[500]         | 750.0000 | 67,250.0000 | 853.5806  | 290.2786    | 834.0000    | 42.0000  | 48;269       | 1.1715       | 107147  | 1          |
| test_benchmark_async_file_handler_write[300]                     | 750.0000 | 34,833.0000 | 878.4348  | 267.1702    | 875.0000    | 83.0000  | 100;515      | 1.1384       | 85405   | 1          |
| test_benchmark_async_file_handler_write[500]                     | 750.0000 | 26,875.0000 | 844.2528  | 180.9212    | 834.0000    | 1.0000   | 57;30548     | 1.1845       | 94483   | 1          |
| test_benchmark_async_file_handler_write_no_flush[1000]           | 750.0000 | 34,584.0000 | 859.0565  | 276.0377    | 834.0000    | 42.0000  | 38;329       | 1.1641       | 86957   | 1          |
| test_benchmark_async_file_handler_write_no_flush[100]            | 750.0000 | 28,834.0000 | 864.6569  | 172.1997    | 875.0000    | 42.0000  | 141;876      | 1.1565       | 105264  | 1          |
| test_benchmark_async_file_handler_write_no_flush[300]            | 750.0000 | 32,750.0000 | 859.9429  | 207.4712    | 875.0000    | 42.0000  | 48;466       | 1.1629       | 90229   | 1          |
| test_benchmark_async_file_handler_write_no_flush[500]            | 750.0000 | 23,958.0000 | 857.3196  | 149.7971    | 834.0000    | 42.0000  | 58;222       | 1.1664       | 93748   | 1          |
| test_benchmark_async_file_handler_write[100]                     | 791.0000 | 38,625.0000 | 912.2558  | 570.9992    | 875.0000    | 42.0000  | 108;365      | 1.0962       | 41451   | 1          |
| test_benchmark_async_file_handler_write_no_flush[2000]           | 791.0000 | 9,875.0000  | 861.4298  | 92.4790     | 875.0000    | 42.0000  | 144;144      | 1.1609       | 67227   | 1          |
| test_benchmark_async_file_handler_write[2000]                    | 792.0000 | 74,625.0000 | 933.4844  | 622.4961    | 917.0000    | 1.0000   | 106;23103    | 1.0713       | 61539   | 1          |

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
