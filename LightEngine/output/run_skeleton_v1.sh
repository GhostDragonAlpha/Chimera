#!/bin/bash
cd E:/PythonChimera || exit 1
python -u LightEngine/demo_skeleton.py --ticks 8000 --tag skeleton_v1 >> LightEngine/output/skeleton_v1_run.log 2>&1
python -u LightEngine/demo_skeleton.py --ticks 8000 --tag skeleton_v1 --cut-ropes >> LightEngine/output/skeleton_v1_run.log 2>&1
