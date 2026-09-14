# A4 readback_probe — results

Adapter: NVIDIA GeForce RTX 4090 (driver 2559295488) · api 1.4.341 · timestampPeriod 1.000 ns · ReBAR: yes

Staging: memory type 3 (HOST_CACHED HOST_COHERENT (device-local heap visible? see types)), alloc 99.7 us, map 1.1 us · one-time source fill+submit 1.580 ms · teardown 278.839 ms

All numbers are ns unless suffixed. median/max over warm iterations (cold row listed separately). Segments are consecutive differences of the ONE continuous timeline.

## img8M_full_idle

- COLD iter0: e2e 81021100 ns (81.021 ms), fence_wait 73604400 ns, gpu_copy 312832 ns

| segment | median ns | max ns |
|---|---:|---:|
| pre_submit | 0 | 100 |
| submit | 29800 | 73800 |
| fence_wait | 455300 | 921400 |
| invalidate | 0 | 0 |
| first_read | 300 | 500 |
| bulk_memcpy | 388000 | 555500 |
| ram_swizzle | 983300 | 1035600 |
| consumer | 6091600 | 6132000 |
| gpu_copy | 312832 | 319488 |
| **e2e_read (request->swizzle_done)** | 1900700 | 2355300 |
| e2e (request->consumer; incl. hash) | 7996900 | 8450100 |
| effective throughput (median e2e) | 1037.2 MB/s | | 

## img4B_full_idle

- COLD iter0: e2e 156500 ns (0.157 ms), fence_wait 133300 ns, gpu_copy 768 ns

| segment | median ns | max ns |
|---|---:|---:|
| pre_submit | 0 | 100 |
| submit | 8500 | 29800 |
| fence_wait | 30100 | 820900 |
| invalidate | 0 | 0 |
| first_read | 100 | 300 |
| bulk_memcpy | 100 | 300 |
| ram_swizzle | 0 | 100 |
| consumer | 0 | 100 |
| gpu_copy | 256 | 512 |
| **e2e_read (request->swizzle_done)** | 38600 | 841700 |
| e2e (request->consumer; incl. hash) | 38600 | 841700 |
| effective throughput (median e2e) | 0.1 MB/s | | 

## buf8M_full_idle

- COLD iter0: e2e 7855100 ns (7.855 ms), fence_wait 383000 ns, gpu_copy 350464 ns

| segment | median ns | max ns |
|---|---:|---:|
| pre_submit | 0 | 100 |
| submit | 26000 | 94700 |
| fence_wait | 532100 | 1201000 |
| invalidate | 0 | 0 |
| first_read | 400 | 500 |
| bulk_memcpy | 379400 | 567000 |
| ram_swizzle | 979500 | 1036900 |
| consumer | 6085700 | 6127500 |
| gpu_copy | 346112 | 361472 |
| **e2e_read (request->swizzle_done)** | 1989900 | 2776600 |
| e2e (request->consumer; incl. hash) | 8091800 | 8859700 |
| effective throughput (median e2e) | 1025.0 MB/s | | 

## buf4B_full_idle

- COLD iter0: e2e 748300 ns (0.748 ms), fence_wait 721800 ns, gpu_copy 512 ns

| segment | median ns | max ns |
|---|---:|---:|
| pre_submit | 0 | 100 |
| submit | 8500 | 22700 |
| fence_wait | 29700 | 367300 |
| invalidate | 0 | 0 |
| first_read | 100 | 300 |
| bulk_memcpy | 100 | 100 |
| ram_swizzle | 0 | 100 |
| consumer | 0 | 100 |
| gpu_copy | 256 | 256 |
| **e2e_read (request->swizzle_done)** | 38500 | 373800 |
| e2e (request->consumer; incl. hash) | 38500 | 373900 |
| effective throughput (median e2e) | 0.1 MB/s | | 

## img8M_noread_idle

- COLD iter0: e2e 354100 ns (0.354 ms), fence_wait 345400 ns, gpu_copy 312576 ns

| segment | median ns | max ns |
|---|---:|---:|
| pre_submit | 0 | 100 |
| submit | 10700 | 22100 |
| fence_wait | 352000 | 1371900 |
| invalidate | 0 | 0 |
| first_read | 0 | 0 |
| bulk_memcpy | 0 | 0 |
| ram_swizzle | 0 | 0 |
| consumer | 0 | 0 |
| gpu_copy | 312832 | 318720 |
| **e2e_read (request->swizzle_done)** | 368100 | 1391200 |
| e2e (request->consumer; incl. hash) | 368100 | 1391200 |

## img4B_noread_idle

- COLD iter0: e2e 39900 ns (0.040 ms), fence_wait 32000 ns, gpu_copy 768 ns

| segment | median ns | max ns |
|---|---:|---:|
| pre_submit | 0 | 100 |
| submit | 8500 | 23500 |
| fence_wait | 30100 | 977300 |
| invalidate | 0 | 0 |
| first_read | 0 | 0 |
| bulk_memcpy | 0 | 0 |
| ram_swizzle | 0 | 0 |
| consumer | 0 | 0 |
| gpu_copy | 256 | 512 |
| **e2e_read (request->swizzle_done)** | 38700 | 996100 |
| e2e (request->consumer; incl. hash) | 38700 | 996100 |

## buf8M_noread_idle

- COLD iter0: e2e 388400 ns (0.388 ms), fence_wait 379900 ns, gpu_copy 345600 ns

| segment | median ns | max ns |
|---|---:|---:|
| pre_submit | 0 | 100 |
| submit | 13000 | 23900 |
| fence_wait | 408500 | 1203200 |
| invalidate | 0 | 0 |
| first_read | 0 | 0 |
| bulk_memcpy | 0 | 0 |
| ram_swizzle | 0 | 0 |
| consumer | 0 | 0 |
| gpu_copy | 351744 | 397568 |
| **e2e_read (request->swizzle_done)** | 419200 | 1214900 |
| e2e (request->consumer; incl. hash) | 419200 | 1214900 |

## buf4B_noread_idle

- COLD iter0: e2e 51700 ns (0.052 ms), fence_wait 32100 ns, gpu_copy 512 ns

| segment | median ns | max ns |
|---|---:|---:|
| pre_submit | 0 | 100 |
| submit | 8400 | 25300 |
| fence_wait | 29900 | 828200 |
| invalidate | 0 | 0 |
| first_read | 0 | 0 |
| bulk_memcpy | 0 | 0 |
| ram_swizzle | 0 | 0 |
| consumer | 0 | 0 |
| gpu_copy | 256 | 256 |
| **e2e_read (request->swizzle_done)** | 38500 | 845100 |
| e2e (request->consumer; incl. hash) | 38500 | 845100 |

## img8M_full_backlog

- COLD iter0: e2e 14608800 ns (14.609 ms), fence_wait 7126400 ns, gpu_copy 313600 ns

| segment | median ns | max ns |
|---|---:|---:|
| pre_submit | 0 | 100 |
| submit | 6000 | 8700 |
| fence_wait | 7212400 | 7994000 |
| invalidate | 0 | 0 |
| first_read | 400 | 700 |
| bulk_memcpy | 402700 | 496600 |
| ram_swizzle | 981300 | 1011000 |
| consumer | 6085100 | 6207400 |
| gpu_copy | 313344 | 1265408 |
| **e2e_read (request->swizzle_done)** | 8584400 | 9339600 |
| e2e (request->consumer; incl. hash) | 14669000 | 15419900 |
| effective throughput (median e2e) | 565.4 MB/s | | 

## img8M_noread_backlog

- COLD iter0: e2e 7363600 ns (7.364 ms), fence_wait 7344800 ns, gpu_copy 536576 ns

| segment | median ns | max ns |
|---|---:|---:|
| pre_submit | 0 | 100 |
| submit | 5600 | 7900 |
| fence_wait | 7246500 | 8184000 |
| invalidate | 0 | 0 |
| first_read | 0 | 0 |
| bulk_memcpy | 0 | 0 |
| ram_swizzle | 0 | 0 |
| consumer | 0 | 0 |
| gpu_copy | 313088 | 952832 |
| **e2e_read (request->swizzle_done)** | 7252500 | 8190200 |
| e2e (request->consumer; incl. hash) | 7252500 | 8190200 |

## buf8M_full_backlog

- COLD iter0: e2e 14947100 ns (14.947 ms), fence_wait 7494100 ns, gpu_copy 347392 ns

| segment | median ns | max ns |
|---|---:|---:|
| pre_submit | 0 | 100 |
| submit | 5900 | 10800 |
| fence_wait | 7306000 | 8276800 |
| invalidate | 0 | 0 |
| first_read | 300 | 500 |
| bulk_memcpy | 393300 | 537800 |
| ram_swizzle | 983500 | 1110400 |
| consumer | 6091900 | 6128400 |
| gpu_copy | 353536 | 1409536 |
| **e2e_read (request->swizzle_done)** | 8684400 | 9611900 |
| e2e (request->consumer; incl. hash) | 14774300 | 15701800 |
| effective throughput (median e2e) | 561.4 MB/s | | 

## buf8M_noread_backlog

- COLD iter0: e2e 6699500 ns (6.699 ms), fence_wait 6693200 ns, gpu_copy 344576 ns

| segment | median ns | max ns |
|---|---:|---:|
| pre_submit | 0 | 100 |
| submit | 5600 | 7000 |
| fence_wait | 7346700 | 8033800 |
| invalidate | 0 | 0 |
| first_read | 0 | 0 |
| bulk_memcpy | 0 | 0 |
| ram_swizzle | 0 | 0 |
| consumer | 0 | 0 |
| gpu_copy | 454144 | 1304576 |
| **e2e_read (request->swizzle_done)** | 7352600 | 8039400 |
| e2e (request->consumer; incl. hash) | 7352600 | 8039400 |

## img4B_full_backlog

- COLD iter0: e2e 6003700 ns (6.004 ms), fence_wait 5997200 ns, gpu_copy 1024 ns

| segment | median ns | max ns |
|---|---:|---:|
| pre_submit | 0 | 100 |
| submit | 5600 | 18100 |
| fence_wait | 6910100 | 7288000 |
| invalidate | 0 | 0 |
| first_read | 400 | 500 |
| bulk_memcpy | 400 | 600 |
| ram_swizzle | 100 | 200 |
| consumer | 0 | 100 |
| gpu_copy | 256 | 1280 |
| **e2e_read (request->swizzle_done)** | 6916700 | 7295200 |
| e2e (request->consumer; incl. hash) | 6916700 | 7295300 |
| effective throughput (median e2e) | 0.0 MB/s | | 

## img4B_noread_backlog

- COLD iter0: e2e 7195000 ns (7.195 ms), fence_wait 7189600 ns, gpu_copy 512 ns

| segment | median ns | max ns |
|---|---:|---:|
| pre_submit | 0 | 100 |
| submit | 5700 | 11700 |
| fence_wait | 6888800 | 7686000 |
| invalidate | 0 | 0 |
| first_read | 0 | 0 |
| bulk_memcpy | 0 | 0 |
| ram_swizzle | 0 | 0 |
| consumer | 0 | 0 |
| gpu_copy | 256 | 768 |
| **e2e_read (request->swizzle_done)** | 6894500 | 7697700 |
| e2e (request->consumer; incl. hash) | 6894500 | 7697700 |

## buf4B_full_backlog

- COLD iter0: e2e 6887000 ns (6.887 ms), fence_wait 6881000 ns, gpu_copy 256 ns

| segment | median ns | max ns |
|---|---:|---:|
| pre_submit | 0 | 100 |
| submit | 5800 | 11700 |
| fence_wait | 6912000 | 7742900 |
| invalidate | 0 | 0 |
| first_read | 400 | 600 |
| bulk_memcpy | 400 | 700 |
| ram_swizzle | 100 | 200 |
| consumer | 0 | 100 |
| gpu_copy | 256 | 768 |
| **e2e_read (request->swizzle_done)** | 6923900 | 7748800 |
| e2e (request->consumer; incl. hash) | 6923900 | 7748900 |
| effective throughput (median e2e) | 0.0 MB/s | | 

## buf4B_noread_backlog

- COLD iter0: e2e 6922100 ns (6.922 ms), fence_wait 6916700 ns, gpu_copy 256 ns

| segment | median ns | max ns |
|---|---:|---:|
| pre_submit | 0 | 100 |
| submit | 5700 | 9300 |
| fence_wait | 6935000 | 7660000 |
| invalidate | 0 | 0 |
| first_read | 0 | 0 |
| bulk_memcpy | 0 | 0 |
| ram_swizzle | 0 | 0 |
| consumer | 0 | 0 |
| gpu_copy | 256 | 768 |
| **e2e_read (request->swizzle_done)** | 6940700 | 7665700 |
| e2e (request->consumer; incl. hash) | 6940700 | 7665700 |

## img8M_full_witness

- COLD iter0: e2e 7912000 ns (7.912 ms), fence_wait 321600 ns, gpu_copy 312576 ns, witness_sig - fwait_return = 109200 ns (neg = witness done BEFORE readback)

| segment | median ns | max ns |
|---|---:|---:|
| pre_submit | 0 | 100 |
| submit | 29100 | 78600 |
| fence_wait | 666900 | 1051800 |
| invalidate | 0 | 0 |
| first_read | 111000 | 115300 |
| bulk_memcpy | 370400 | 438300 |
| ram_swizzle | 965200 | 993200 |
| consumer | 6086700 | 6130900 |
| gpu_copy | 312832 | 313088 |
| **e2e_read (request->swizzle_done)** | 2139900 | 2608100 |
| e2e (request->consumer; incl. hash) | 8257100 | 8687100 |
| effective throughput (median e2e) | 1004.5 MB/s | | 

WITNESS: median(witness_sig - fwait_return) = 110500 ns (negative => independent work completed BEFORE the readback did); witness already done at first poll in 0/19 warm iters.

## img8M_full_idlesleep

- COLD iter0: e2e 8207100 ns (8.207 ms), fence_wait 745900 ns, gpu_copy 312832 ns

| segment | median ns | max ns |
|---|---:|---:|
| pre_submit | 0 | 100 |
| submit | 35800 | 42000 |
| fence_wait | 653000 | 1003900 |
| invalidate | 0 | 0 |
| first_read | 300 | 400 |
| bulk_memcpy | 367000 | 450700 |
| ram_swizzle | 961700 | 979600 |
| consumer | 6112400 | 6127000 |
| gpu_copy | 313344 | 313600 |
| **e2e_read (request->swizzle_done)** | 2021800 | 2454400 |
| e2e (request->consumer; incl. hash) | 8134200 | 8572600 |
| effective throughput (median e2e) | 1019.7 MB/s | | 

## img8M_full_nofence_idle

- COLD iter0: e2e 7472600 ns (7.473 ms), fence_wait 0 ns, gpu_copy 313344 ns

| segment | median ns | max ns |
|---|---:|---:|
| pre_submit | 0 | 100 |
| submit | 19100 | 1287900 |
| fence_wait | 0 | 0 |
| invalidate | 0 | 0 |
| first_read | 200 | 300 |
| bulk_memcpy | 390700 | 506900 |
| ram_swizzle | 981700 | 1111700 |
| consumer | 6086600 | 6130100 |
| gpu_copy | 313344 | 317696 |
| **e2e_read (request->swizzle_done)** | 1412400 | 2643000 |
| e2e (request->consumer; incl. hash) | 7503600 | 8732400 |
| effective throughput (median e2e) | 1105.4 MB/s | | 

## img8M_full_nofence_backlog

- COLD iter0: e2e 7427700 ns (7.428 ms), fence_wait 0 ns, gpu_copy 527616 ns

| segment | median ns | max ns |
|---|---:|---:|
| pre_submit | 0 | 100 |
| submit | 4800 | 25400 |
| fence_wait | 0 | 0 |
| invalidate | 0 | 0 |
| first_read | 300 | 400 |
| bulk_memcpy | 374500 | 524300 |
| ram_swizzle | 984700 | 1074000 |
| consumer | 6078800 | 6139000 |
| gpu_copy | 313600 | 1070080 |
| **e2e_read (request->swizzle_done)** | 1369500 | 1501900 |
| e2e (request->consumer; incl. hash) | 7455500 | 7596700 |
| effective throughput (median e2e) | 1112.5 MB/s | | 

## img8M_full_pressure

- COLD iter0: e2e 110113700 ns (110.114 ms), fence_wait 102650200 ns, gpu_copy 312832 ns

| segment | median ns | max ns |
|---|---:|---:|
| pre_submit | 0 | 100 |
| submit | 6500 | 16100 |
| fence_wait | 101129300 | 108154100 |
| invalidate | 0 | 0 |
| first_read | 400 | 700 |
| bulk_memcpy | 377500 | 443500 |
| ram_swizzle | 960500 | 1163900 |
| consumer | 6075700 | 6121900 |
| gpu_copy | 318208 | 1055488 |
| **e2e_read (request->swizzle_done)** | 102501000 | 109486800 |
| e2e (request->consumer; incl. hash) | 108575100 | 115547800 |
| effective throughput (median e2e) | 76.4 MB/s | | 

