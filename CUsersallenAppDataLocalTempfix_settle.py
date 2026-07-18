import os

filepath = r'E:\PythonChimera\Chimera\Source\Chimera\ProceduralGenerated\Tests\WeightShiftAnimationTests.cpp'

with open(filepath, 'r') as f:
    content = f.read()

# Find and replace the broken settle test section
old_section = '''		// Trigger a weight shift by decelerating
		Component->CurrentVelocity = FVector(400.0f, 0.0f, 0.0f);
		Component->UpdateWeightShift(0.016f);


		// Advance time to let weight shift build up (sample at peak, not pre-swing)'''

new_section = '''		// Trigger a weight shift by decelerating
		Component->CurrentVelocity = FVector(400.0f, 0.0f, 0.0f);
		Component->UpdateWeightShift(0.016f);

		Component->CurrentVelocity = FVector(0.0f, 0.0f, 0.0f);
		Component->UpdateWeightShift(0.016f);

		// Advance time to let weight shift build up (sample at peak, not pre-swing)'''

if old_section in content:
    content = content.replace(old_section, new_section)
    with open(filepath, 'w') as f:
        f.write(content)
    print("Fixed settle test section")
else:
    print("Pattern not found - checking current content...")
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'Trigger a weight shift' in line or 'Advance time to let' in line:
            print(f"Line {i+1}: {repr(line)}")
