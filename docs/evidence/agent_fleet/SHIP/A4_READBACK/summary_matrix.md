# A4 readback_probe — results

Adapter: NVIDIA GeForce RTX 4090 (driver 2559295488) · api 1.4.341 · timestampPeriod 1.000 ns · ReBAR: yes

Staging: memory type 3 (HOST_CACHED HOST_COHERENT (device-local heap visible? see types)), alloc 96.2 us, map 1.2 us · one-time source fill+submit 1.589 ms · teardown 111.286 ms

All numbers are ns unless suffixed. median/max over warm iterations (cold row listed separately). Segments are consecutive differences of the ONE continuous timeline.

## img8M_full_idle

- COLD iter0: e2e 85924000 ns (85.924 ms), fence_wait 78466300 ns, gpu_copy 312576 ns

| segment | median ns | max ns |
|---|---:|---:|
| pre_submit | 0 | 100 |
| submit | 26200 | 53500 |
| fence_wait | 754900 | 1178400 |
| invalidate | 0 | 0 |
| first_read | 300 | 500 |
| bulk_memcpy | 376300 | 498200 |
| ram_swizzle | 980200 | 1094600 |
| consumer | 6113200 | 6209100 |
| gpu_copy | 312576 | 313088 |
| **e2e_read (request->swizzle_done)** | 2155500 | 2556300 |
| e2e (request->consumer; incl. hash) | 8239500 | 8706100 |
| effective throughput (median e2e) | 1006.7 MB/s | | 

## img4B_full_idle

- COLD iter0: e2e 258300 ns (0.258 ms), fence_wait 237800 ns, gpu_copy 768 ns

| segment | median ns | max ns |
|---|---:|---:|
| pre_submit | 0 | 100 |
| submit | 8300 | 24300 |
| fence_wait | 30200 | 361400 |
| invalidate | 0 | 0 |
| first_read | 100 | 300 |
| bulk_memcpy | 100 | 200 |
| ram_swizzle | 0 | 100 |
| consumer | 0 | 100 |
| gpu_copy | 256 | 256 |
| **e2e_read (request->swizzle_done)** | 38700 | 368200 |
| e2e (request->consumer; incl. hash) | 38700 | 368200 |
| effective throughput (median e2e) | 0.1 MB/s | | 

## buf8M_full_idle

- COLD iter0: e2e 7929400 ns (7.929 ms), fence_wait 391400 ns, gpu_copy 348672 ns

| segment | median ns | max ns |
|---|---:|---:|
| pre_submit | 0 | 100 |
| submit | 28900 | 69500 |
| fence_wait | 570700 | 1153700 |
| invalidate | 0 | 0 |
| first_read | 400 | 700 |
| bulk_memcpy | 388800 | 539300 |
| ram_swizzle | 981900 | 1031400 |
| consumer | 6097500 | 6245500 |
| gpu_copy | 344832 | 356608 |
| **e2e_read (request->swizzle_done)** | 1987400 | 2576100 |
| e2e (request->consumer; incl. hash) | 8086300 | 8645800 |
| effective throughput (median e2e) | 1025.7 MB/s | | 

## buf4B_full_idle

- COLD iter0: e2e 436500 ns (0.436 ms), fence_wait 410700 ns, gpu_copy 768 ns

| segment | median ns | max ns |
|---|---:|---:|
| pre_submit | 0 | 100 |
| submit | 8200 | 20900 |
| fence_wait | 30400 | 231100 |
| invalidate | 0 | 0 |
| first_read | 100 | 200 |
| bulk_memcpy | 100 | 200 |
| ram_swizzle | 0 | 100 |
| consumer | 0 | 100 |
| gpu_copy | 256 | 256 |
| **e2e_read (request->swizzle_done)** | 39000 | 248300 |
| e2e (request->consumer; incl. hash) | 39100 | 248300 |
| effective throughput (median e2e) | 0.1 MB/s | | 

## img8M_noread_idle

- COLD iter0: e2e 364300 ns (0.364 ms), fence_wait 345800 ns, gpu_copy 312576 ns

| segment | median ns | max ns |
|---|---:|---:|
| pre_submit | 0 | 100 |
| submit | 18600 | 35200 |
| fence_wait | 358000 | 1387400 |
| invalidate | 0 | 0 |
| first_read | 0 | 0 |
| bulk_memcpy | 0 | 0 |
| ram_swizzle | 0 | 0 |
| consumer | 0 | 0 |
| gpu_copy | 312576 | 317184 |
| **e2e_read (request->swizzle_done)** | 381900 | 1400400 |
| e2e (request->consumer; incl. hash) | 381900 | 1400400 |

## img4B_noread_idle

- COLD iter0: e2e 51100 ns (0.051 ms), fence_wait 33400 ns, gpu_copy 512 ns

| segment | median ns | max ns |
|---|---:|---:|
| pre_submit | 0 | 100 |
| submit | 8600 | 25600 |
| fence_wait | 30300 | 831600 |
| invalidate | 0 | 0 |
| first_read | 0 | 0 |
| bulk_memcpy | 0 | 0 |
| ram_swizzle | 0 | 0 |
| consumer | 0 | 0 |
| gpu_copy | 256 | 512 |
| **e2e_read (request->swizzle_done)** | 39200 | 839000 |
| e2e (request->consumer; incl. hash) | 39200 | 839000 |

## buf8M_noread_idle

- COLD iter0: e2e 397100 ns (0.397 ms), fence_wait 388400 ns, gpu_copy 351232 ns

| segment | median ns | max ns |
|---|---:|---:|
| pre_submit | 0 | 100 |
| submit | 17100 | 31200 |
| fence_wait | 419000 | 1205500 |
| invalidate | 0 | 0 |
| first_read | 0 | 0 |
| bulk_memcpy | 0 | 0 |
| ram_swizzle | 0 | 0 |
| consumer | 0 | 0 |
| gpu_copy | 354048 | 393728 |
| **e2e_read (request->swizzle_done)** | 434000 | 1214700 |
| e2e (request->consumer; incl. hash) | 434000 | 1214700 |

## buf4B_noread_idle

- COLD iter0: e2e 238600 ns (0.239 ms), fence_wait 230100 ns, gpu_copy 512 ns

| segment | median ns | max ns |
|---|---:|---:|
| pre_submit | 0 | 100 |
| submit | 8700 | 26300 |
| fence_wait | 30400 | 628900 |
| invalidate | 0 | 0 |
| first_read | 0 | 0 |
| bulk_memcpy | 0 | 0 |
| ram_swizzle | 0 | 0 |
| consumer | 0 | 0 |
| gpu_copy | 256 | 512 |
| **e2e_read (request->swizzle_done)** | 40000 | 636800 |
| e2e (request->consumer; incl. hash) | 40000 | 636800 |

## img8M_full_backlog

- COLD iter0: e2e 14132400 ns (14.132 ms), fence_wait 6682100 ns, gpu_copy 455168 ns

| segment | median ns | max ns |
|---|---:|---:|
| pre_submit | 0 | 100 |
| submit | 5700 | 13000 |
| fence_wait | 7261400 | 8138500 |
| invalidate | 0 | 0 |
| first_read | 400 | 700 |
| bulk_memcpy | 373700 | 481000 |
| ram_swizzle | 980500 | 1195900 |
| consumer | 6100800 | 6204300 |
| gpu_copy | 312832 | 1192448 |
| **e2e_read (request->swizzle_done)** | 8639800 | 9469300 |
| e2e (request->consumer; incl. hash) | 14767900 | 15528400 |
| effective throughput (median e2e) | 561.7 MB/s | | 

## img8M_noread_backlog

- COLD iter0: e2e 7683200 ns (7.683 ms), fence_wait 7675000 ns, gpu_copy 312320 ns

| segment | median ns | max ns |
|---|---:|---:|
| pre_submit | 0 | 100 |
| submit | 5400 | 11400 |
| fence_wait | 7291600 | 8040900 |
| invalidate | 0 | 0 |
| first_read | 0 | 0 |
| bulk_memcpy | 0 | 0 |
| ram_swizzle | 0 | 0 |
| consumer | 0 | 0 |
| gpu_copy | 312832 | 1142272 |
| **e2e_read (request->swizzle_done)** | 7296800 | 8046600 |
| e2e (request->consumer; incl. hash) | 7296800 | 8046600 |

## buf8M_full_backlog

- COLD iter0: e2e 14756900 ns (14.757 ms), fence_wait 7237900 ns, gpu_copy 1205760 ns

| segment | median ns | max ns |
|---|---:|---:|
| pre_submit | 0 | 100 |
| submit | 5700 | 10900 |
| fence_wait | 7231600 | 7817700 |
| invalidate | 0 | 0 |
| first_read | 400 | 600 |
| bulk_memcpy | 373400 | 552700 |
| ram_swizzle | 978600 | 1180900 |
| consumer | 6117200 | 6237400 |
| gpu_copy | 346112 | 1307904 |
| **e2e_read (request->swizzle_done)** | 8594500 | 9180500 |
| e2e (request->consumer; incl. hash) | 14712700 | 15357600 |
| effective throughput (median e2e) | 563.8 MB/s | | 

## buf8M_noread_backlog

- COLD iter0: e2e 7106400 ns (7.106 ms), fence_wait 7099700 ns, gpu_copy 685312 ns

| segment | median ns | max ns |
|---|---:|---:|
| pre_submit | 0 | 100 |
| submit | 5300 | 10900 |
| fence_wait | 7304900 | 7762700 |
| invalidate | 0 | 0 |
| first_read | 0 | 0 |
| bulk_memcpy | 0 | 0 |
| ram_swizzle | 0 | 0 |
| consumer | 0 | 0 |
| gpu_copy | 346880 | 1206016 |
| **e2e_read (request->swizzle_done)** | 7310200 | 7768000 |
| e2e (request->consumer; incl. hash) | 7310200 | 7768000 |

## img4B_full_backlog

- COLD iter0: e2e 6224200 ns (6.224 ms), fence_wait 6218000 ns, gpu_copy 768 ns

| segment | median ns | max ns |
|---|---:|---:|
| pre_submit | 0 | 100 |
| submit | 5300 | 21400 |
| fence_wait | 6852300 | 7372400 |
| invalidate | 0 | 0 |
| first_read | 400 | 600 |
| bulk_memcpy | 400 | 700 |
| ram_swizzle | 100 | 100 |
| consumer | 0 | 100 |
| gpu_copy | 256 | 1280 |
| **e2e_read (request->swizzle_done)** | 6858500 | 7379400 |
| e2e (request->consumer; incl. hash) | 6858500 | 7379400 |
| effective throughput (median e2e) | 0.0 MB/s | | 

## img4B_noread_backlog

- COLD iter0: e2e 6540300 ns (6.540 ms), fence_wait 6535000 ns, gpu_copy 256 ns

| segment | median ns | max ns |
|---|---:|---:|
| pre_submit | 0 | 100 |
| submit | 5500 | 7800 |
| fence_wait | 6891100 | 7718100 |
| invalidate | 0 | 0 |
| first_read | 0 | 0 |
| bulk_memcpy | 0 | 0 |
| ram_swizzle | 0 | 0 |
| consumer | 0 | 0 |
| gpu_copy | 256 | 512 |
| **e2e_read (request->swizzle_done)** | 6898900 | 7723100 |
| e2e (request->consumer; incl. hash) | 6898900 | 7723100 |

## buf4B_full_backlog

- COLD iter0: e2e 7250500 ns (7.250 ms), fence_wait 7244600 ns, gpu_copy 256 ns

| segment | median ns | max ns |
|---|---:|---:|
| pre_submit | 0 | 100 |
| submit | 5600 | 9200 |
| fence_wait | 6933300 | 7539500 |
| invalidate | 0 | 0 |
| first_read | 400 | 600 |
| bulk_memcpy | 400 | 700 |
| ram_swizzle | 100 | 200 |
| consumer | 0 | 100 |
| gpu_copy | 256 | 768 |
| **e2e_read (request->swizzle_done)** | 6939800 | 7546500 |
| e2e (request->consumer; incl. hash) | 6939800 | 7546500 |
| effective throughput (median e2e) | 0.0 MB/s | | 

## buf4B_noread_backlog

- COLD iter0: e2e 6896900 ns (6.897 ms), fence_wait 6891300 ns, gpu_copy 256 ns

| segment | median ns | max ns |
|---|---:|---:|
| pre_submit | 0 | 100 |
| submit | 5600 | 6100 |
| fence_wait | 6861900 | 7480000 |
| invalidate | 0 | 0 |
| first_read | 0 | 0 |
| bulk_memcpy | 0 | 0 |
| ram_swizzle | 0 | 0 |
| consumer | 0 | 0 |
| gpu_copy | 256 | 1024 |
| **e2e_read (request->swizzle_done)** | 6868000 | 7486200 |
| e2e (request->consumer; incl. hash) | 6868000 | 7486200 |

## img8M_full_witness

- COLD iter0: e2e 8843300 ns (8.843 ms), fence_wait 1175000 ns, gpu_copy 312320 ns, witness_sig - fwait_return = 110400 ns (neg = witness done BEFORE readback)

| segment | median ns | max ns |
|---|---:|---:|
| pre_submit | 0 | 100 |
| submit | 28100 | 64600 |
| fence_wait | 632500 | 1166100 |
| invalidate | 0 | 0 |
| first_read | 114600 | 117200 |
| bulk_memcpy | 370900 | 399800 |
| ram_swizzle | 976500 | 1029100 |
| consumer | 6116800 | 6234400 |
| gpu_copy | 312576 | 312832 |
| **e2e_read (request->swizzle_done)** | 2216700 | 2643700 |
| e2e (request->consumer; incl. hash) | 8301700 | 8760700 |
| effective throughput (median e2e) | 999.1 MB/s | | 

WITNESS: median(witness_sig - fwait_return) = 114100 ns (negative => independent work completed BEFORE the readback did); witness already done at first poll in 0/19 warm iters.

## img8M_full_idlesleep

- COLD iter0: e2e 8010400 ns (8.010 ms), fence_wait 573200 ns, gpu_copy 312576 ns

| segment | median ns | max ns |
|---|---:|---:|
| pre_submit | 0 | 100 |
| submit | 35300 | 64700 |
| fence_wait | 870500 | 1148400 |
| invalidate | 0 | 0 |
| first_read | 300 | 500 |
| bulk_memcpy | 373800 | 395000 |
| ram_swizzle | 966200 | 1003300 |
| consumer | 6100100 | 6109900 |
| gpu_copy | 313600 | 313856 |
| **e2e_read (request->swizzle_done)** | 2247300 | 2603400 |
| e2e (request->consumer; incl. hash) | 8352200 | 8668200 |
| effective throughput (median e2e) | 993.1 MB/s | | 

## img8M_full_nofence_idle

- COLD iter0: e2e 7468700 ns (7.469 ms), fence_wait 0 ns, gpu_copy 315392 ns

| segment | median ns | max ns |
|---|---:|---:|
| pre_submit | 0 | 100 |
| submit | 19300 | 1292000 |
| fence_wait | 0 | 0 |
| invalidate | 0 | 0 |
| first_read | 300 | 500 |
| bulk_memcpy | 400900 | 585700 |
| ram_swizzle | 985600 | 1042000 |
| consumer | 6077900 | 6120200 |
| gpu_copy | 313856 | 320256 |
| **e2e_read (request->swizzle_done)** | 1413900 | 2633500 |
| e2e (request->consumer; incl. hash) | 7488900 | 8749800 |
| effective throughput (median e2e) | 1107.6 MB/s | | 

## img8M_full_nofence_backlog

- COLD iter0: e2e 7410700 ns (7.411 ms), fence_wait 0 ns, gpu_copy 532480 ns

| segment | median ns | max ns |
|---|---:|---:|
| pre_submit | 0 | 100 |
| submit | 4900 | 31800 |
| fence_wait | 0 | 0 |
| invalidate | 0 | 0 |
| first_read | 300 | 600 |
| bulk_memcpy | 373700 | 486200 |
| ram_swizzle | 973000 | 1009800 |
| consumer | 6084500 | 6211300 |
| gpu_copy | 422912 | 1286400 |
| **e2e_read (request->swizzle_done)** | 1351500 | 1526600 |
| e2e (request->consumer; incl. hash) | 7433900 | 7610100 |
| effective throughput (median e2e) | 1115.8 MB/s | | 

