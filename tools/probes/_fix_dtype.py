"""Fix int8 -> uint16 in dirty_set_economy.py."""
import pathlib

p = pathlib.Path("e:/PythonChimera/tools/probes/dirty_set_economy.py")
s = p.read_text()
old_count = s.count("dtype=np.int8")
new_count = s.count("dtype=np.uint16")
print(f"Before: int8={old_count}, uint16={new_count}")
s2 = s.replace("dtype=np.int8", "dtype=np.uint16")
after_int8 = s2.count("dtype=np.int8")
after_uint16 = s2.count("dtype=np.uint16")
print(f"After:  int8={after_int8}, uint16={after_uint16}")
assert after_int8 == 0, f"Still {after_int8} int8 occurrences!"
p.write_text(s2)
print("Fixed.")
