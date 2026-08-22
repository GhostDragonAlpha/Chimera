"""Dump the gsplat Parser normalization transform for a dataset.
Usage: dump_norm_transform.py <data_dir> <out.npy>
"""
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools" / "gsplat" / "examples"))

from datasets.colmap import Parser  # noqa: E402

data, out = sys.argv[1], sys.argv[2]
p = Parser(data_dir=data, factor=1, normalize=True, test_every=8)
np.save(out, p.transform)
print("saved", out)
print(p.transform)
