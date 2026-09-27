| bone | sha256 (16) | tri | d_own mm (in?) | chain links d mm | site anchors mm | verdict |
|---|---|---|---|---|---|---|
| pisiform | a8cfa7c74c1f551d | 7056 | 1.22 (in) | - | FCU-P4 16.83 (course) | ADJACENCY-SUPPORTED |
| lunate | 225cbfc34bc7e246 | 3720 | 3.39 (in) | - | - | ADJACENCY-SUPPORTED |
| scaphoid | 0a016dd1497f6719 | 3654 | 2.18 (in) | - | - | ADJACENCY-SUPPORTED |
| triquetrum | 8828f38da02f8a9f | 3172 | 3.56 (in) | - | - | ADJACENCY-SUPPORTED |
| hamate | d880faf00df1cc47 | 5166 | 3.78 (in) | ->4mc 31.34F; ->5mc 26.65F | - | OUT(link-fail) |
| capitate | 51c4ff14860a267f | 4746 | 4.22 (in) | ->3mc 30.40F | - | OUT(link-fail) |
| trapezoid | 3a68fabd59a87208 | 2832 | 3.52 (in) | ->2mc 28.85F | - | OUT(link-fail) |
| trapezium | f130696c1dfec4d0 | 4492 | 4.54 (in) | ->1mc 4.53F | - | OUT(link-fail) |
| 1mc | b75e58243a2005af | 5744 | 2.23 (in) | ->thumbprox 4.48F; on trapezium 4.53F | - | OUT(link-fail) |
| 2mc | ac3286bfb7281a7d | 8360 | 2.59 (in) | ->2proxph 4.07F; on trapezoid 28.85F | ECRL-P4 0.80; FCR-P3 0.69 | OUT(link-fail) |
| 3mc | eaa77802c8afe5a3 | 8086 | 2.08 (in) | ->3proxph 4.15F; on capitate 30.40F | ECRB-P4 0.51 | OUT(link-fail) |
| 4mc | ad2fe21562879512 | 6486 | 1.97 (in) | ->4proxph 3.47P; on hamate 31.34F | - | CHAIN-PASS |
| 5mc | 46c75922ddc94f98 | 5016 | 1.77 (in) | ->5proxph 3.62F; on hamate 26.65F | ECU-P6 0.06 | OUT(link-fail) |
| thumbprox | d55ea0de846c5acf | 3948 | 6.42 (out) | ->thumbdist 2.16P; on 1mc 4.48F | - | CHAIN-PASS |
| thumbdist | 95b059723be971e7 | 3484 | 3.66 (out) | on thumbprox 2.16P | - | CHAIN-PASS |
| 2proxph | 041bf5a60e9376c0 | 5122 | 6.68 (out) | ->2midph 2.55P; on 2mc 4.07F | - | CHAIN-PASS |
| 2midph | 074318c92e652ba0 | 2000 | 3.81 (out) | ->2distph 1.45P; on 2proxph 2.55P | - | CHAIN-PASS |
| 2distph | 39fca93724345208 | 2206 | 2.66 (out) | on 2midph 1.45P | - | CHAIN-PASS |
| 3proxph | 48094bce62d115ae | 5604 | 6.44 (out) | ->3midph 2.11P; on 3mc 4.15F | - | CHAIN-PASS |
| 3midph | 5e0ef3d76f2f99f9 | 2234 | 3.22 (out) | ->3distph 1.35P; on 3proxph 2.11P | - | CHAIN-PASS |
| 3distph | d5ecddeac9b45720 | 2546 | 2.29 (out) | on 3midph 1.35P | - | CHAIN-PASS |
| 4proxph | eea82e95eb50e934 | 5264 | 6.07 (out) | ->4midph 1.99P; on 4mc 3.47P | - | CHAIN-PASS |
| 4midph | 98ecb5ad76749abd | 2204 | 3.31 (out) | ->4distph 1.45P; on 4proxph 1.99P | - | CHAIN-PASS |
| 4distph | 02f01c191dfc86ab | 2608 | 2.43 (out) | on 4midph 1.45P | - | CHAIN-PASS |
| 5proxph | b04672ea67df7403 | 3742 | 6.66 (out) | ->5midph 2.08P; on 5mc 3.62F | - | CHAIN-PASS |
| 5midph | d383a1f058224f71 | 1566 | 3.61 (out) | ->5distph 1.38P; on 5proxph 2.08P | - | CHAIN-PASS |
| 5distph | a2ca70efdb0a5e59 | 2979 | 2.50 (out) | on 5midph 1.38P | - | CHAIN-PASS |
