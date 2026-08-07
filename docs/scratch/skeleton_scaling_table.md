# StandingHuman bone scaling table

Body plan: height = 1.80 m, mass = 80.0 kg
Lattice spacing = 0.05 lu
d_eq = 0.0484 lu
Bone compressive strength = 1.700e+08 Pa (ANATOMY-DATUM)
Lu-to-meter ratio = 2.710135e-03 m/lu  (1 m = 368.99 lu)

Scale derivation:
- Required area per bone A = (load_fraction * mass * g) / sigma.
- Midshaft is a hollow tube with wall thickness = 1 grain = lattice spacing.
- The smallest required area A_min sets the scale so that the smallest
  hollow tube is exactly 3 grains across (1-grain wall + 1-grain void + 1-grain wall).

The diameters below are structural minima from compressive strength; real bones
are larger because of buckling margins, safety factors, and muscle attachment.

| name | length (m) | length (lu) | D_out (m) | D_out (lu) | shell (lu) | solid end (lu) | design load (kg) | grains | prox | dist | moment resolution |
|---|---|---|---|---|---|---|---|---|---|---|---|
| skull | 0.2160 | 79.701 | 0.000894 | 0.330 | 0.05 | 0.330 | 5.60 | 28,264 | suture | ball-cup | head weight resolved through the cervical stack; no cantilever |
| mandible | 0.1440 | 53.134 | 0.002846 | 1.050 | 0.05 | 1.050 | 20.00 | 78,680 | saddle | hinge | bite force resolved by paired condylar compression + masseter/temporalis ropes |
| vertebra C1 | 0.0206 | 7.591 | 0.000894 | 0.330 | 0.05 | 0.330 | 5.60 | 2,891 | ball-cup | saddle | skull weight -> cervical compression stack |
| vertebra C2 | 0.0206 | 7.591 | 0.001177 | 0.434 | 0.05 | 0.434 | 7.69 | 4,277 | saddle | saddle | moment resolved into compression pair with adjacent vertebra + posterior rope/ligament arc |
| vertebra C3 | 0.0206 | 7.591 | 0.001460 | 0.539 | 0.05 | 0.539 | 9.77 | 5,965 | saddle | saddle | moment resolved into compression pair with adjacent vertebra + posterior rope/ligament arc |
| vertebra C4 | 0.0206 | 7.591 | 0.001743 | 0.643 | 0.05 | 0.643 | 11.86 | 8,041 | saddle | saddle | moment resolved into compression pair with adjacent vertebra + posterior rope/ligament arc |
| vertebra C5 | 0.0206 | 7.591 | 0.002026 | 0.747 | 0.05 | 0.747 | 13.95 | 10,590 | saddle | saddle | moment resolved into compression pair with adjacent vertebra + posterior rope/ligament arc |
| vertebra C6 | 0.0206 | 7.591 | 0.002308 | 0.852 | 0.05 | 0.852 | 16.03 | 13,697 | saddle | saddle | moment resolved into compression pair with adjacent vertebra + posterior rope/ligament arc |
| vertebra C7 | 0.0206 | 7.591 | 0.002591 | 0.956 | 0.05 | 0.956 | 18.12 | 17,449 | saddle | saddle | moment resolved into compression pair with adjacent vertebra + posterior rope/ligament arc |
| vertebra T1 | 0.0240 | 8.856 | 0.002874 | 1.060 | 0.05 | 1.060 | 20.21 | 23,538 | saddle | saddle | moment resolved into compression pair with adjacent vertebra + posterior rope/ligament arc |
| vertebra T2 | 0.0240 | 8.856 | 0.003157 | 1.165 | 0.05 | 1.165 | 22.30 | 29,002 | saddle | saddle | moment resolved into compression pair with adjacent vertebra + posterior rope/ligament arc |
| vertebra T3 | 0.0240 | 8.856 | 0.003440 | 1.269 | 0.05 | 1.269 | 24.38 | 35,367 | saddle | saddle | moment resolved into compression pair with adjacent vertebra + posterior rope/ligament arc |
| vertebra T4 | 0.0240 | 8.856 | 0.003722 | 1.373 | 0.05 | 1.373 | 26.47 | 42,720 | saddle | saddle | moment resolved into compression pair with adjacent vertebra + posterior rope/ligament arc |
| vertebra T5 | 0.0240 | 8.856 | 0.004005 | 1.478 | 0.05 | 1.478 | 28.56 | 51,146 | saddle | saddle | moment resolved into compression pair with adjacent vertebra + posterior rope/ligament arc |
| vertebra T6 | 0.0240 | 8.856 | 0.004288 | 1.582 | 0.05 | 1.582 | 30.64 | 60,729 | saddle | saddle | moment resolved into compression pair with adjacent vertebra + posterior rope/ligament arc |
| vertebra T7 | 0.0240 | 8.856 | 0.004571 | 1.687 | 0.05 | 1.687 | 32.73 | 71,558 | saddle | saddle | moment resolved into compression pair with adjacent vertebra + posterior rope/ligament arc |
| vertebra T8 | 0.0240 | 8.856 | 0.004853 | 1.791 | 0.05 | 1.791 | 34.82 | 83,716 | saddle | saddle | moment resolved into compression pair with adjacent vertebra + posterior rope/ligament arc |
| vertebra T9 | 0.0240 | 8.856 | 0.005136 | 1.895 | 0.05 | 1.895 | 36.90 | 97,290 | saddle | saddle | moment resolved into compression pair with adjacent vertebra + posterior rope/ligament arc |
| vertebra T10 | 0.0240 | 8.856 | 0.005419 | 2.000 | 0.05 | 2.000 | 38.99 | 112,364 | saddle | saddle | moment resolved into compression pair with adjacent vertebra + posterior rope/ligament arc |
| vertebra T11 | 0.0240 | 8.856 | 0.005702 | 2.104 | 0.05 | 2.104 | 41.08 | 129,026 | saddle | saddle | moment resolved into compression pair with adjacent vertebra + posterior rope/ligament arc |
| vertebra T12 | 0.0240 | 8.856 | 0.005985 | 2.208 | 0.05 | 2.208 | 43.17 | 147,360 | saddle | saddle | moment resolved into compression pair with adjacent vertebra + posterior rope/ligament arc |
| vertebra L1 | 0.0288 | 10.627 | 0.006267 | 2.313 | 0.05 | 2.313 | 45.25 | 172,489 | saddle | saddle | moment resolved into compression pair with adjacent vertebra + posterior rope/ligament arc |
| vertebra L2 | 0.0288 | 10.627 | 0.006550 | 2.417 | 0.05 | 2.417 | 47.34 | 194,657 | saddle | saddle | moment resolved into compression pair with adjacent vertebra + posterior rope/ligament arc |
| vertebra L3 | 0.0288 | 10.627 | 0.006833 | 2.521 | 0.05 | 2.521 | 49.43 | 218,755 | saddle | saddle | moment resolved into compression pair with adjacent vertebra + posterior rope/ligament arc |
| vertebra L4 | 0.0288 | 10.627 | 0.007116 | 2.626 | 0.05 | 2.626 | 51.51 | 244,868 | saddle | saddle | moment resolved into compression pair with adjacent vertebra + posterior rope/ligament arc |
| vertebra L5 | 0.0288 | 10.627 | 0.007399 | 2.730 | 0.05 | 2.730 | 53.60 | 273,082 | saddle | saddle | upper-body load -> sacral arch compression |
| sacrum | 0.1080 | 39.850 | 0.007399 | 2.730 | 0.05 | 2.730 | 53.60 | 371,501 | saddle | ball-cup | lumbar load resolved into the two pelvic columns (the pelvic arch) |
| coccyx | 0.0540 | 19.925 | 0.001220 | 0.450 | 0.05 | 0.450 | 8.00 | 10,710 | suture | free | seated contact load resolved through the sacrum; no cantilever outboard |
| rib pair 1 | 0.3240 | 119.551 | 0.000407 | 0.150 | 0.05 | 0.150 | 2.00 | 15,029 | hinge | hinge | thoracic wall load resolved as an arch between vertebra and sternum |
| rib pair 2 | 0.3240 | 119.551 | 0.000407 | 0.150 | 0.05 | 0.150 | 2.00 | 15,029 | hinge | hinge | thoracic wall load resolved as an arch between vertebra and sternum |
| rib pair 3 | 0.3240 | 119.551 | 0.000407 | 0.150 | 0.05 | 0.150 | 2.00 | 15,029 | hinge | hinge | thoracic wall load resolved as an arch between vertebra and sternum |
| rib pair 4 | 0.3240 | 119.551 | 0.000407 | 0.150 | 0.05 | 0.150 | 2.00 | 15,029 | hinge | hinge | thoracic wall load resolved as an arch between vertebra and sternum |
| rib pair 5 | 0.3240 | 119.551 | 0.000407 | 0.150 | 0.05 | 0.150 | 2.00 | 15,029 | hinge | hinge | thoracic wall load resolved as an arch between vertebra and sternum |
| rib pair 6 | 0.3240 | 119.551 | 0.000407 | 0.150 | 0.05 | 0.150 | 2.00 | 15,029 | hinge | hinge | thoracic wall load resolved as an arch between vertebra and sternum |
| rib pair 7 | 0.3240 | 119.551 | 0.000407 | 0.150 | 0.05 | 0.150 | 2.00 | 15,029 | hinge | hinge | thoracic wall load resolved as an arch between vertebra and sternum |
| rib pair 8 | 0.3240 | 119.551 | 0.000407 | 0.150 | 0.05 | 0.150 | 2.00 | 15,029 | hinge | hinge | thoracic wall load resolved as an arch between vertebra and sternum |
| rib pair 9 | 0.3240 | 119.551 | 0.000407 | 0.150 | 0.05 | 0.150 | 2.00 | 15,029 | hinge | hinge | thoracic wall load resolved as an arch between vertebra and sternum |
| rib pair 10 | 0.3240 | 119.551 | 0.000407 | 0.150 | 0.05 | 0.150 | 2.00 | 15,029 | hinge | hinge | thoracic wall load resolved as an arch between vertebra and sternum |
| rib pair 11 | 0.3240 | 119.551 | 0.000407 | 0.150 | 0.05 | 0.150 | 2.00 | 15,029 | hinge | hinge | thoracic wall load resolved as an arch between vertebra and sternum |
| rib pair 12 | 0.3240 | 119.551 | 0.000407 | 0.150 | 0.05 | 0.150 | 2.00 | 15,029 | hinge | hinge | thoracic wall load resolved as an arch between vertebra and sternum |
| sternum | 0.1620 | 59.776 | 0.001220 | 0.450 | 0.05 | 0.450 | 8.00 | 30,741 | saddle | suture | rib-cage arch compression resolved through the costal cartilages |
| clavicle pair | 0.0900 | 33.209 | 0.005556 | 2.050 | 0.05 | 2.050 | 40.00 | 181,420 | saddle | ball-cup | suspension load resolved to sternum and scapula; no shaft capture |
| scapula pair | 0.1620 | 59.776 | 0.005556 | 2.050 | 0.05 | 2.050 | 40.00 | 248,190 | saddle | ball-cup | arm load resolved through rotator-cuff ropes to the thorax |
| humerus pair | 0.3420 | 126.193 | 0.005556 | 2.050 | 0.05 | 2.050 | 40.00 | 415,115 | ball-cup | hinge | elbow load resolved by biceps/triceps ropes across the shoulder |
| radius/ulna pair | 0.2520 | 92.984 | 0.005556 | 2.050 | 0.05 | 2.050 | 40.00 | 331,652 | hinge | saddle | hand load resolved by forearm flexor/extensor ropes |
| carpals group | 0.0540 | 19.925 | 0.005556 | 2.050 | 0.05 | 2.050 | 40.00 | 148,035 | saddle | saddle | wrist load resolved through ligament ropes to radius/ulna |
| metacarpals group | 0.1260 | 46.492 | 0.005556 | 2.050 | 0.05 | 2.050 | 40.00 | 214,805 | saddle | hinge | grip load resolved by digital flexor ropes |
| hand phalanges group | 0.1080 | 39.850 | 0.005556 | 2.050 | 0.05 | 2.050 | 40.00 | 198,112 | hinge | hinge | grip contact load resolved by extensor/flexor ropes |
| pelvis pair | 0.2520 | 92.984 | 0.003767 | 1.390 | 0.05 | 1.390 | 26.80 | 185,644 | saddle | ball-cup | spine load resolved into the two femoral columns (the pelvic arch) |
| femur pair | 0.4410 | 162.723 | 0.005556 | 2.050 | 0.05 | 2.050 | 40.00 | 506,923 | ball-cup | hinge | hip-to-knee load resolved by hip abductor/adductor ropes |
| patella pair | 0.0540 | 19.925 | 0.005556 | 2.050 | 0.05 | 2.050 | 40.00 | 148,035 | saddle | saddle | sesamoid in quadriceps rope; knee moment resolved by patellar tendon rope |
| tibia pair | 0.4500 | 166.043 | 0.005556 | 2.050 | 0.05 | 2.050 | 40.00 | 515,270 | hinge | hinge | knee-to-ankle load resolved by Achilles and collateral ropes |
| fibula pair | 0.3960 | 146.118 | 0.001220 | 0.450 | 0.05 | 0.450 | 8.00 | 74,141 | hinge | hinge | lateral malleolus load resolved by interosseous membrane rope |
| tarsals group | 0.1080 | 39.850 | 0.005556 | 2.050 | 0.05 | 2.050 | 40.00 | 198,112 | hinge | saddle | ankle reaction resolved into the plantar arch |
| metatarsals group | 0.1440 | 53.134 | 0.005556 | 2.050 | 0.05 | 2.050 | 40.00 | 231,497 | saddle | hinge | arch load resolved by plantar ligament ropes |
| foot phalanges group | 0.0900 | 33.209 | 0.002846 | 1.050 | 0.05 | 1.050 | 20.00 | 53,641 | hinge | hinge | push-off load resolved by digital flexor/extensor ropes |

**Total grain count:** 6,401,413

**Top 5 grain consumers:**
- tibia pair: 515,270 grains
- femur pair: 506,923 grains
- humerus pair: 415,115 grains
- sacrum: 371,501 grains
- radius/ulna pair: 331,652 grains

**No 1-grain-shell rule failures at the derived scale.**
