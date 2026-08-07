# StandingHuman bone scaling table (budget-first)

Body plan: height = 1.80 m, mass = 80.0 kg
Kernel budget N_BUDGET = 50,000 grains
Budget source: LightEngine/output/bench_kernel_report.md
d_eq (grain spacing) = 0.0484 lu
Bone compressive strength = 1.700e+08 Pa (ANATOMY-DATUM)

**Resolved scale:** 2.699280e-02 m/lu  (1 m = 37.05 lu)
**Physical grain spacing:** 1.306452e-03 m

## Scale derivation

The iteration is over the lu-to-meter scale `lambda`.  For each candidate
scale, every bone is assigned to the highest fidelity rung it can still resolve:

- rung (a): hollow tube + solid ends, requires outer diameter >= 3 grains.
- rung (b): solid rod of the derived compression area, minimum 2x2 grains.
- rung (c): 2x2 solid rod; structural area is overbuilt.

The chosen scale is the coarsest one that brings the total (bones + cups + ropes + plate)
under the kernel budget while keeping every bone on its highest possible rung.

## Candidate scale scan

| lambda (m/lu) | grain (m) | total | bones | cups | ropes | plate | rungs (a/b/c) |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1.3716e-03 | 6.6384e-05 | 205,795,596 | 195,630,029 | 2,172,930 | 38,229 | 7,954,408 | 52/0/0 |
| 1.7190e-03 | 8.3201e-05 | 61,186,544 | 55,187,008 | 900,980 | 30,506 | 5,068,050 | 51/1/0 |
| 2.2398e-03 | 1.0841e-04 | 16,931,098 | 13,594,619 | 326,542 | 23,422 | 2,986,515 | 51/0/1 |
| 2.7997e-03 | 1.3551e-04 | 6,699,837 | 4,625,975 | 141,920 | 18,736 | 1,913,206 | 50/1/1 |
| 2.8071e-03 | 1.3587e-04 | 6,631,748 | 4,570,143 | 140,470 | 18,695 | 1,902,440 | 38/13/1 |
| 2.9096e-03 | 1.4082e-04 | 5,797,008 | 3,884,739 | 123,230 | 18,031 | 1,771,008 | 38/12/2 |
| 3.5089e-03 | 1.6983e-04 | 3,038,475 | 1,742,503 | 63,078 | 14,950 | 1,217,944 | 37/13/2 |
| 3.6466e-03 | 1.7650e-04 | 2,696,103 | 1,498,632 | 55,150 | 14,401 | 1,127,920 | 37/1/14 |
| 3.9594e-03 | 1.9164e-04 | 2,113,398 | 1,100,215 | 41,678 | 13,265 | 958,240 | 37/0/15 |
| 4.6848e-03 | 2.2675e-04 | 1,335,038 | 614,920 | 24,180 | 11,203 | 684,735 | 35/2/15 |
| 4.9624e-03 | 2.4018e-04 | 1,152,555 | 511,059 | 20,262 | 10,580 | 610,654 | 33/4/15 |
| 5.4888e-03 | 2.6566e-04 | 900,124 | 376,066 | 15,098 | 9,568 | 499,392 | 33/2/17 |
| 5.5995e-03 | 2.7101e-04 | 858,342 | 354,702 | 14,264 | 9,376 | 480,000 | 32/3/17 |
| 5.8716e-03 | 2.8418e-04 | 768,172 | 309,510 | 12,518 | 8,945 | 437,199 | 30/5/17 |
| 6.1892e-03 | 2.9956e-04 | 680,082 | 267,558 | 10,900 | 8,492 | 393,132 | 30/3/19 |
| 6.8180e-03 | 3.2999e-04 | 547,366 | 207,166 | 8,598 | 7,701 | 323,901 | 29/4/19 |
| 6.8792e-03 | 3.3295e-04 | 536,873 | 202,476 | 8,418 | 7,640 | 318,339 | 28/5/19 |
| 7.0179e-03 | 3.3967e-04 | 513,602 | 192,474 | 8,034 | 7,492 | 305,602 | 28/4/20 |
| 7.3936e-03 | 3.5785e-04 | 459,700 | 169,697 | 7,162 | 7,111 | 275,730 | 28/2/22 |
| 7.7570e-03 | 3.7544e-04 | 415,767 | 151,658 | 6,480 | 6,777 | 250,852 | 27/3/22 |
| 7.9274e-03 | 3.8369e-04 | 397,276 | 144,309 | 6,214 | 6,628 | 240,125 | 27/2/23 |
| 8.4275e-03 | 4.0789e-04 | 350,488 | 125,909 | 5,540 | 6,239 | 212,800 | 26/3/23 |
| 8.5451e-03 | 4.1358e-04 | 340,563 | 122,155 | 5,406 | 6,152 | 206,850 | 25/4/23 |
| 8.8535e-03 | 4.2851e-04 | 317,404 | 113,226 | 5,076 | 5,935 | 193,167 | 25/3/24 |
| 8.8996e-03 | 4.3074e-04 | 313,951 | 111,978 | 5,046 | 5,911 | 191,016 | 24/4/24 |
| 9.2665e-03 | 4.4850e-04 | 289,481 | 102,920 | 4,716 | 5,669 | 176,176 | 23/5/24 |
| 9.3478e-03 | 4.5243e-04 | 284,660 | 101,096 | 4,658 | 5,626 | 173,280 | 23/4/25 |
| 9.7755e-03 | 4.7314e-04 | 260,460 | 92,365 | 4,352 | 5,388 | 158,355 | 22/5/25 |
| 9.9356e-03 | 4.8088e-04 | 252,219 | 89,439 | 4,256 | 5,296 | 153,228 | 21/6/25 |
| 1.0185e-02 | 4.9297e-04 | 240,448 | 85,196 | 4,114 | 5,167 | 145,971 | 21/5/26 |
| 1.0249e-02 | 4.9604e-04 | 237,498 | 84,177 | 4,082 | 5,137 | 144,102 | 20/6/26 |
| 1.0562e-02 | 5.1122e-04 | 223,948 | 79,461 | 3,932 | 4,980 | 135,575 | 19/7/26 |
| 1.0579e-02 | 5.1203e-04 | 223,364 | 79,224 | 3,908 | 4,976 | 135,256 | 19/6/27 |
| 1.0959e-02 | 5.3041e-04 | 208,999 | 74,164 | 3,758 | 4,797 | 126,280 | 18/7/27 |
| 1.1096e-02 | 5.3706e-04 | 204,045 | 72,481 | 3,702 | 4,742 | 123,120 | 17/8/27 |
| 1.1154e-02 | 5.3985e-04 | 202,291 | 71,793 | 3,672 | 4,717 | 122,109 | 17/7/28 |
| 1.1326e-02 | 5.4818e-04 | 196,414 | 69,852 | 3,610 | 4,646 | 118,306 | 17/6/29 |
| 1.1682e-02 | 5.6538e-04 | 185,401 | 66,117 | 3,512 | 4,507 | 111,265 | 16/7/29 |
| 1.1716e-02 | 5.6704e-04 | 184,049 | 65,770 | 3,480 | 4,495 | 110,304 | 15/8/29 |
| 1.2027e-02 | 5.8208e-04 | 175,722 | 62,850 | 3,396 | 4,382 | 105,094 | 15/7/30 |
| 1.2252e-02 | 5.9299e-04 | 169,795 | 60,874 | 3,338 | 4,291 | 101,292 | 14/8/30 |
| 1.2362e-02 | 5.9831e-04 | 166,928 | 59,971 | 3,318 | 4,267 | 99,372 | 14/7/31 |
| 1.2521e-02 | 6.0600e-04 | 163,097 | 58,679 | 3,280 | 4,208 | 96,930 | 13/8/31 |
| 1.2688e-02 | 6.1412e-04 | 158,914 | 57,374 | 3,224 | 4,152 | 94,164 | 8/13/31 |
| 1.2765e-02 | 6.1784e-04 | 157,403 | 56,794 | 3,198 | 4,131 | 93,280 | 7/14/31 |
| 1.2845e-02 | 6.2169e-04 | 155,550 | 56,218 | 3,182 | 4,100 | 92,050 | 7/13/32 |
| 1.3007e-02 | 6.2952e-04 | 152,276 | 55,113 | 3,158 | 4,045 | 89,960 | 7/12/33 |
| 1.3259e-02 | 6.4174e-04 | 147,005 | 53,477 | 3,110 | 3,973 | 86,445 | 6/13/33 |
| 1.3317e-02 | 6.4456e-04 | 146,015 | 53,108 | 3,100 | 3,955 | 85,852 | 6/12/34 |
| 1.3621e-02 | 6.5926e-04 | 140,054 | 51,290 | 3,052 | 3,872 | 81,840 | 5/13/34 |
| 1.3735e-02 | 6.6478e-04 | 137,947 | 50,641 | 3,030 | 3,834 | 80,442 | 4/14/34 |
| 1.3918e-02 | 6.7363e-04 | 134,920 | 49,638 | 3,006 | 3,787 | 78,489 | 4/13/35 |
| 1.4195e-02 | 6.8704e-04 | 130,322 | 48,190 | 2,974 | 3,712 | 75,446 | 3/14/35 |
| 1.4209e-02 | 6.8771e-04 | 130,238 | 48,121 | 2,966 | 3,705 | 75,446 | 3/13/36 |
| 1.4494e-02 | 7.0150e-04 | 125,532 | 46,724 | 2,942 | 3,636 | 72,230 | 2/14/36 |
| 1.4494e-02 | 7.0150e-04 | 125,521 | 46,719 | 2,936 | 3,636 | 72,230 | 1/15/36 |
| 1.4641e-02 | 7.0860e-04 | 123,459 | 46,031 | 2,914 | 3,597 | 70,917 | 0/16/36 |
| 1.5073e-02 | 7.2953e-04 | 117,785 | 44,136 | 2,874 | 3,500 | 67,275 | 0/15/37 |
| 1.5493e-02 | 7.4988e-04 | 112,428 | 42,455 | 2,842 | 3,402 | 63,729 | 0/14/38 |
| 1.5692e-02 | 7.5951e-04 | 109,875 | 41,700 | 2,828 | 3,355 | 61,992 | 0/13/39 |
| 1.5903e-02 | 7.6968e-04 | 107,470 | 41,084 | 2,790 | 3,317 | 60,279 | 0/8/44 |
| 1.6301e-02 | 7.8899e-04 | 103,429 | 40,006 | 2,776 | 3,239 | 57,408 | 0/7/45 |
| 1.6691e-02 | 8.0784e-04 | 99,726 | 39,001 | 2,760 | 3,155 | 54,810 | 0/6/46 |
| 1.7071e-02 | 8.2626e-04 | 96,457 | 38,082 | 2,746 | 3,093 | 52,536 | 0/5/47 |
| 1.7444e-02 | 8.4428e-04 | 93,036 | 37,229 | 2,734 | 3,021 | 50,052 | 0/4/48 |
| 1.7808e-02 | 8.6192e-04 | 90,194 | 36,431 | 2,726 | 2,967 | 48,070 | 0/3/49 |
| 1.8165e-02 | 8.7920e-04 | 87,698 | 35,702 | 2,716 | 2,904 | 46,376 | 0/2/50 |
| 1.8165e-02 | 8.7920e-04 | 87,692 | 35,702 | 2,710 | 2,904 | 46,376 | 0/1/51 |
| **2.6993e-02** | **1.3065e-03** | **49,850** | **24,018** | **2,704** | **1,960** | **21,168** | **0/0/52** |

## Final budget breakdown

- Bones: 24,018 grains
- Joint cups: 2,704 grains
- Ropes (43 from rope_network.py): 1,960 grains
- Ground plate: 21,168 grains
- **Total: 49,850 grains**

Rung counts: (a) = 0, (b) = 0, (c) = 52

## Bone table

| name | length (m) | length (lu) | D_out (m) | D_out (lu) | shell (lu) | solid end (lu) | design load (kg) | grains | rung | prox | dist | moment resolution |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| skull | 0.2160 | 8.002 | 0.002613 | 0.097 | solid | 8.002 | 5.60 | 662 | c | suture | ball-cup | head weight resolved through the cervical stack; no cantilever |
| vertebra C1 | 0.0206 | 0.762 | 0.002613 | 0.097 | solid | 0.762 | 5.60 | 63 | c | ball-cup | saddle | skull weight -> cervical compression stack |
| vertebra C2 | 0.0206 | 0.762 | 0.002613 | 0.097 | solid | 0.762 | 7.69 | 63 | c | saddle | saddle | moment resolved into compression pair with adjacent vertebra + posterior rope/ligament arc |
| vertebra C3 | 0.0206 | 0.762 | 0.002613 | 0.097 | solid | 0.762 | 9.77 | 63 | c | saddle | saddle | moment resolved into compression pair with adjacent vertebra + posterior rope/ligament arc |
| vertebra C4 | 0.0206 | 0.762 | 0.002613 | 0.097 | solid | 0.762 | 11.86 | 63 | c | saddle | saddle | moment resolved into compression pair with adjacent vertebra + posterior rope/ligament arc |
| vertebra C5 | 0.0206 | 0.762 | 0.002613 | 0.097 | solid | 0.762 | 13.95 | 63 | c | saddle | saddle | moment resolved into compression pair with adjacent vertebra + posterior rope/ligament arc |
| vertebra C6 | 0.0206 | 0.762 | 0.002613 | 0.097 | solid | 0.762 | 16.03 | 63 | c | saddle | saddle | moment resolved into compression pair with adjacent vertebra + posterior rope/ligament arc |
| vertebra C7 | 0.0206 | 0.762 | 0.002613 | 0.097 | solid | 0.762 | 18.12 | 63 | c | saddle | saddle | moment resolved into compression pair with adjacent vertebra + posterior rope/ligament arc |
| vertebra T1 | 0.0240 | 0.889 | 0.002613 | 0.097 | solid | 0.889 | 20.21 | 74 | c | saddle | saddle | moment resolved into compression pair with adjacent vertebra + posterior rope/ligament arc |
| vertebra T2 | 0.0240 | 0.889 | 0.002613 | 0.097 | solid | 0.889 | 22.30 | 74 | c | saddle | saddle | moment resolved into compression pair with adjacent vertebra + posterior rope/ligament arc |
| vertebra T3 | 0.0240 | 0.889 | 0.002613 | 0.097 | solid | 0.889 | 24.38 | 74 | c | saddle | saddle | moment resolved into compression pair with adjacent vertebra + posterior rope/ligament arc |
| vertebra T4 | 0.0240 | 0.889 | 0.002613 | 0.097 | solid | 0.889 | 26.47 | 74 | c | saddle | saddle | moment resolved into compression pair with adjacent vertebra + posterior rope/ligament arc |
| vertebra T5 | 0.0240 | 0.889 | 0.002613 | 0.097 | solid | 0.889 | 28.56 | 74 | c | saddle | saddle | moment resolved into compression pair with adjacent vertebra + posterior rope/ligament arc |
| vertebra T6 | 0.0240 | 0.889 | 0.002613 | 0.097 | solid | 0.889 | 30.64 | 74 | c | saddle | saddle | moment resolved into compression pair with adjacent vertebra + posterior rope/ligament arc |
| vertebra T7 | 0.0240 | 0.889 | 0.002613 | 0.097 | solid | 0.889 | 32.73 | 74 | c | saddle | saddle | moment resolved into compression pair with adjacent vertebra + posterior rope/ligament arc |
| vertebra T8 | 0.0240 | 0.889 | 0.002613 | 0.097 | solid | 0.889 | 34.82 | 74 | c | saddle | saddle | moment resolved into compression pair with adjacent vertebra + posterior rope/ligament arc |
| vertebra T9 | 0.0240 | 0.889 | 0.002613 | 0.097 | solid | 0.889 | 36.90 | 74 | c | saddle | saddle | moment resolved into compression pair with adjacent vertebra + posterior rope/ligament arc |
| vertebra T10 | 0.0240 | 0.889 | 0.002613 | 0.097 | solid | 0.889 | 38.99 | 74 | c | saddle | saddle | moment resolved into compression pair with adjacent vertebra + posterior rope/ligament arc |
| vertebra T11 | 0.0240 | 0.889 | 0.002613 | 0.097 | solid | 0.889 | 41.08 | 74 | c | saddle | saddle | moment resolved into compression pair with adjacent vertebra + posterior rope/ligament arc |
| vertebra T12 | 0.0240 | 0.889 | 0.002613 | 0.097 | solid | 0.889 | 43.17 | 74 | c | saddle | saddle | moment resolved into compression pair with adjacent vertebra + posterior rope/ligament arc |
| vertebra L1 | 0.0288 | 1.067 | 0.002613 | 0.097 | solid | 1.067 | 45.25 | 89 | c | saddle | saddle | moment resolved into compression pair with adjacent vertebra + posterior rope/ligament arc |
| vertebra L2 | 0.0288 | 1.067 | 0.002613 | 0.097 | solid | 1.067 | 47.34 | 89 | c | saddle | saddle | moment resolved into compression pair with adjacent vertebra + posterior rope/ligament arc |
| vertebra L3 | 0.0288 | 1.067 | 0.002613 | 0.097 | solid | 1.067 | 49.43 | 89 | c | saddle | saddle | moment resolved into compression pair with adjacent vertebra + posterior rope/ligament arc |
| vertebra L4 | 0.0288 | 1.067 | 0.002613 | 0.097 | solid | 1.067 | 51.51 | 89 | c | saddle | saddle | moment resolved into compression pair with adjacent vertebra + posterior rope/ligament arc |
| vertebra L5 | 0.0288 | 1.067 | 0.002613 | 0.097 | solid | 1.067 | 53.60 | 89 | c | saddle | saddle | upper-body load -> sacral arch compression |
| sacrum | 0.1080 | 4.001 | 0.002613 | 0.097 | solid | 4.001 | 53.60 | 331 | c | saddle | ball-cup | lumbar load resolved into the two pelvic columns (the pelvic arch) |
| rib pair 1 | 0.3240 | 12.003 | 0.002613 | 0.097 | solid | 12.003 | 2.00 | 992 | c | hinge | hinge | thoracic wall load resolved as an arch between vertebra and sternum |
| rib pair 2 | 0.3240 | 12.003 | 0.002613 | 0.097 | solid | 12.003 | 2.00 | 992 | c | hinge | hinge | thoracic wall load resolved as an arch between vertebra and sternum |
| rib pair 3 | 0.3240 | 12.003 | 0.002613 | 0.097 | solid | 12.003 | 2.00 | 992 | c | hinge | hinge | thoracic wall load resolved as an arch between vertebra and sternum |
| rib pair 4 | 0.3240 | 12.003 | 0.002613 | 0.097 | solid | 12.003 | 2.00 | 992 | c | hinge | hinge | thoracic wall load resolved as an arch between vertebra and sternum |
| rib pair 5 | 0.3240 | 12.003 | 0.002613 | 0.097 | solid | 12.003 | 2.00 | 992 | c | hinge | hinge | thoracic wall load resolved as an arch between vertebra and sternum |
| rib pair 6 | 0.3240 | 12.003 | 0.002613 | 0.097 | solid | 12.003 | 2.00 | 992 | c | hinge | hinge | thoracic wall load resolved as an arch between vertebra and sternum |
| rib pair 7 | 0.3240 | 12.003 | 0.002613 | 0.097 | solid | 12.003 | 2.00 | 992 | c | hinge | hinge | thoracic wall load resolved as an arch between vertebra and sternum |
| rib pair 8 | 0.3240 | 12.003 | 0.002613 | 0.097 | solid | 12.003 | 2.00 | 992 | c | hinge | hinge | thoracic wall load resolved as an arch between vertebra and sternum |
| rib pair 9 | 0.3240 | 12.003 | 0.002613 | 0.097 | solid | 12.003 | 2.00 | 992 | c | hinge | hinge | thoracic wall load resolved as an arch between vertebra and sternum |
| rib pair 10 | 0.3240 | 12.003 | 0.002613 | 0.097 | solid | 12.003 | 2.00 | 992 | c | hinge | hinge | thoracic wall load resolved as an arch between vertebra and sternum |
| rib pair 11 | 0.3240 | 12.003 | 0.002613 | 0.097 | solid | 12.003 | 2.00 | 992 | c | hinge | hinge | thoracic wall load resolved as an arch between vertebra and sternum |
| rib pair 12 | 0.3240 | 12.003 | 0.002613 | 0.097 | solid | 12.003 | 2.00 | 992 | c | hinge | hinge | thoracic wall load resolved as an arch between vertebra and sternum |
| sternum | 0.1620 | 6.002 | 0.002613 | 0.097 | solid | 6.002 | 8.00 | 496 | c | saddle | suture | rib-cage arch compression resolved through the costal cartilages |
| clavicle pair | 0.0900 | 3.334 | 0.002613 | 0.097 | solid | 3.334 | 4.00 | 276 | c | saddle | ball-cup | arm mass resolved to sternum and scapula; no shaft capture |
| scapula pair | 0.1620 | 6.002 | 0.002613 | 0.097 | solid | 6.002 | 4.00 | 496 | c | saddle | ball-cup | arm mass resolved through rotator-cuff ropes to the thorax |
| humerus pair | 0.3420 | 12.670 | 0.002613 | 0.097 | solid | 12.670 | 2.16 | 1,048 | c | ball-cup | hinge | elbow load resolved by biceps/triceps ropes across the shoulder |
| radius/ulna pair | 0.2520 | 9.336 | 0.002613 | 0.097 | solid | 9.336 | 1.28 | 772 | c | hinge | saddle | hand mass resolved by forearm flexor/extensor ropes |
| hand mass | 0.1080 | 4.001 | 0.002613 | 0.097 | solid | 4.001 | 0.48 | 331 | c | saddle | hinge | individual hand bones are below budget; only combined COM is retained |
| pelvis pair | 0.2520 | 9.336 | 0.002613 | 0.097 | solid | 9.336 | 26.80 | 772 | c | saddle | ball-cup | spine load resolved into the two femoral columns (the pelvic arch) |
| femur pair | 0.4410 | 16.338 | 0.002613 | 0.097 | solid | 16.338 | 40.00 | 1,351 | c | ball-cup | hinge | hip-to-knee load resolved by hip abductor/adductor ropes |
| patella pair | 0.0540 | 2.001 | 0.002613 | 0.097 | solid | 2.001 | 40.00 | 166 | c | saddle | saddle | sesamoid in quadriceps rope; knee moment resolved by patellar tendon rope |
| tibia pair | 0.4500 | 16.671 | 0.002613 | 0.097 | solid | 16.671 | 40.00 | 1,378 | c | hinge | hinge | knee-to-ankle load resolved by Achilles and collateral ropes |
| fibula pair | 0.3960 | 14.671 | 0.002613 | 0.097 | solid | 14.671 | 8.00 | 1,213 | c | hinge | hinge | lateral malleolus load resolved by interosseous membrane rope |
| tarsals group | 0.1080 | 4.001 | 0.002613 | 0.097 | solid | 4.001 | 40.00 | 331 | c | hinge | saddle | ankle reaction resolved into the plantar arch |
| metatarsals group | 0.1440 | 5.335 | 0.002613 | 0.097 | solid | 5.335 | 40.00 | 441 | c | saddle | hinge | arch load resolved by plantar ligament ropes |
| forefoot mass | 0.0900 | 3.334 | 0.002613 | 0.097 | solid | 3.334 | 20.00 | 276 | c | hinge | hinge | individual toe bones are below budget; only combined push-off COM is retained |
