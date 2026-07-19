"""Fix non-ASCII chars in dialogos.py for Windows cp1252 compatibility."""
text = open("dialogos.py", encoding="utf-8").read()

replacements = {
    "\u00d7": "x",
    "\u2014": "--",
    "\u2018": "'",
    "\u2019": "'",
    "\u201c": '"',
    "\u201d": '"',
    "\u2192": "->",
    "\u2500": "-",
    "\u2502": "|",
    "\u2550": "=",
    "\u2557": "+",
    "\u255a": "+",
    "\u255d": "+",
    "\u2560": "+",
    "\u2563": "+",
    "\u2566": "+",
    "\u2569": "+",
    "\u256c": "+",
    "\u2588": "#",
}

for old, new in replacements.items():
    text = text.replace(old, new)

open("dialogos.py", "w", encoding="utf-8").write(text)
print(f"Fixed. File size: {len(text)} bytes")
