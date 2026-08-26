# Visual Validation Guide - Genetics Pipeline Renders

<!-- CHIMERA-LAW -->
> **RULE 0 — EVERY MEMBRANE IS A THEORY. STATE IT BEFORE YOU BUILD IT.** Three parts, all three
> required: a **STATEMENT** someone could disagree with · a **PREDICTION** you have not measured
> yet · a **FALSIFIER** named *before* the run. **A description survives any result; a theory can
> lose.** No falsifier, no build.
>
> **RULE 1 — DERIVE IT BEFORE YOU TRAIN IT.** A parameter sweep is an admission the derivation was
> not done. Before any run, any sweep, any "let's try N variants": trace the variables and show the
> equations close. If you are choosing a number, you broke the chain and substituted taste for a
> law. Ask what QUESTION each variant answers — if the answer is "which number is best", STOP.
>
> **RULE 0 IS ENFORCED AT S-1 VALIDATE** — every port tested alone, and `port_test()` REFUSES to
> register a test that names no falsifier. The model it feeds: `docs/THE_COMPILER.md` — ports →
> primitives → programs → parser → runtime → calibration.
>
> **[docs/THE_LAW.md](docs/THE_LAW.md)** · the method: `docs/THE_WORKFLOW.md` §0
> · 26 rules: `Chimera/docs/EXPERIMENTAL_METHOD.md` · gate: `python tools/training_gate.py`
<!-- CHIMERA-LAW -->

## 🌐 Access Your Rendered Images

**HTTP Server is running at:** `http://localhost:8080`

The server displays all 5 rendered materials in a gallery with heritability data.

### How to View:
1. Open your web browser
2. Navigate to: `http://localhost:8080`
3. Examine each material's children variants carefully

---

## 🔍 What to Look For (Validation Checklist)

### ✅ GOOD SIGNS - Proceed with Confidence

**Material Coherence:**
- [ ] All children in a family look like variations of the same material type
- [ ] Bonsai children all look vegetative/plant-like
- [ ] Stump children all look woody/organic
- [ ] Bicycle/Truck children both look metallic (even if different colors)
- [ ] Plush children look fabric/textile-like

**Appropriate Variation:**
- [ ] Children are NOT identical to each other
- [ ] Children show natural variation within material family
- [ ] No extreme outliers or clamped values
- [ ] Colors stay within reasonable ranges for the material type

**Visual Quality:**
- [ ] No obvious rendering artifacts (strange patterns, banding)
- [ ] No clamping issues (pure white/black, zero size splats)
- [ ] Shapes look intentional and coherent
- [ ] Overall appearance is natural-looking

### ❌ PROBLEM SIGNS - Need Debugging

**Material Incoherence:**
- [ ] Children don't resemble their parent material type
- [ ] Some children look completely different from others in same family
- [ ] Colors are unnatural or clamped to extremes

**Excessive Variation:**
- [ ] Children look like random noise rather than variants
- [ ] Extreme size differences (some huge, some tiny)
- [ ] Anisotropy values seem wrong (flat vs. extremely elongated)

**Rendering Issues:**
- [ ] Visible artifacts or glitches in the images
- [ ] Clamping to pure white/black colors
- [ ] Zero-size splats creating holes or gaps

---

## 📊 Expected Results by Material Type

### 1. Bonsai Vegetative 🌿
**Expected appearance:** Plant-like structures with green/brown colors, organic shapes
**Variation range:** Different sizes, orientations, color shades (all within plant palette)
**Should look like:** Variations of bonsai trees/plants

### 2. Stump Wood 🪵
**Expected appearance:** Woody texture, brown/tan colors, rough surfaces
**Variation range:** Different wood grain patterns, size variations
**Should look like:** Variations of wooden stumps/logs

### 3. Bicycle Metallic 🚲
**Expected appearance:** Metallic surfaces, likely silver/chrome with some color accents
**Variation range:** Different metallic finishes, slight color variations
**Should look like:** Variations of metallic bicycle parts

### 4. Plush Fabric 🧸
**Expected appearance:** Soft textile texture, fabric-like appearance
**Variation range:** Different fabric colors, weave patterns
**Should look like:** Variations of plush/fabric materials

### 5. Truck Metallic 🚚
**Expected appearance:** Heavy metallic surfaces, industrial metal look
**Variation range:** Different metal types, surface finishes
**Should look like:** Variations of truck/metal vehicle parts

---

## 🎯 Decision Framework

### IF VISUAL VALIDATION PASSES (Most Likely) ✅

**Immediate Actions:**
1. **Document success:** Update `task_progress.md` with "Visual validation: PASSED"
2. **Commit changes:** `git add -A; git commit -m "Visual validation passed for 5 materials"; git push origin master`
3. **Record in DNA graph:** Use `graphify_record observe` to document visual results

**Next Session Priorities:**
1. **Process remaining critical materials:** Grass tuft, rock sample, pure metal, ice
2. **Test two-parent recombination:** Full sexual reproduction pipeline with `recombine()`
3. **Integrate with membrane shapes:** Apply class genomes to sphere/plane/cylinder via `clothe()`

**Medium-Term Goals:**
1. Build comprehensive material library for game content
2. Train splat compositions against class genome distributions
3. Enable procedural generation with genetic diversity

### IF VISUAL VALIDATION FAILS ⚠️

**Debug Checklist:**
1. **Check spread parameter:** Too high? Try `spread=0.5` instead of `1.0` in `spawn_children()`
2. **Verify heritability estimates:** Are they reasonable? Check variance decomposition
3. **Examine child generation:** Look at `build_child()` parameters (form, n_splats)
4. **Review render settings:** Check `render_orbit()` elevation and view count

**Immediate Fixes:**
1. Adjust `spread` parameter in `spawn_children()` call
2. Modify `n_splats` or form selection in `build_child()`
3. Re-render with corrected parameters
4. Validate again

---

## 📈 Technical Reference

### Render Statistics
- **Total renders:** 90 views (6 per material × 5 materials)
- **GPU acceleration:** NVIDIA GeForce RTX 4090
- **Render time:** 400-577ms per material
- **Splat count:** ~79K splats per render
- **Image size:** ~220-270KB each

### Heritability Ranges by Material Type
| Material | Color h² | Size h² | Other Traits |
|----------|----------|---------|--------------|
| Bonsai Vegetative | 0.83-0.89 | 0.08 | Aniso: 0.58, Opacity: 0.52 |
| Stump Wood | 0.78+ | 0.03 | Opacity: 0.84, Aniso: 0.20 |
| Bicycle Metallic | 0.15-0.20 | 0.01 | Opacity: 0.86, Aniso: 0.01 |
| Plush Fabric | 0.72-0.81 | 0.10 | Aniso: 0.04, Opacity: 0.05 |
| Truck Metallic | 0.58-0.65 | 0.003 | Aniso: 0.64, Opacity: 0.06 |

---

## 🚀 Quick Commands

```bash
# Start HTTP server (if not running)
cd E:/PythonChimera && python view_renders.py

# Check render files exist
dir Saved/SplatEmit\*.png

# View DNA graph records
cd E:/PythonChimera/Chimera && python -m core.graphify_record observe --derived-from "visual_validation" --verdict "passed|needs_debugging"

# Commit validation results
git add -A && git commit -m "Visual validation completed for 5 materials" && git push origin master
```

---

## 📝 Validation Log Template

```markdown
## Visual Validation Results - [Date]

**Status:** PASSED / FAILED

**Materials Validated:**
- [ ] Bonsai Vegetative: Coherent variants? Yes/No
- [ ] Stump Wood: Coherent variants? Yes/No  
- [ ] Bicycle Metallic: Coherent variants? Yes/No
- [ ] Plush Fabric: Coherent variants? Yes/No
- [ ] Truck Metallic: Coherent variants? Yes/No

**Notes:**
[Add any observations about material coherence, variation quality, rendering artifacts]

**Next Steps:**
[Proceed to next materials / Debug parameters / Other actions]
```

---

## 🎉 Conclusion

The genetics pipeline has successfully generated 90 rendered views across 5 diverse materials. Visual validation is the final gate before proceeding to expansion and integration phases.

**Remember:** The renders should look like coherent material variants, not random noise. Each family should show appropriate variation while maintaining material identity.

---

*Validation guide created on 2026-07-23. Server running at http://localhost:8080*
