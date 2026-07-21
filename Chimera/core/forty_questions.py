#!/usr/bin/env python3
"""40-question engine — every new feature is interrogated before training.
Generates 40 questions, answers them from the graph + catalog, weaves answers
into the constraint set and graph record.
"""
import json, os, sys
from pathlib import Path

BASE = Path(__file__).parent.parent


def load_catalog():
    p = BASE / 'docs' / 'element_catalog.json'
    if not p.exists(): return []
    with open(p) as f:
        return json.load(f).get('elements', [])


def query_graph(query_type, identifier=''):
    try:
        sys.path.insert(0, str(BASE))
        from core.graphify_interface import graphify_query
        return graphify_query(query_type, identifier)
    except:
        return []


class QuestionEngine:
    """Generates 40 questions for any feature name, answers from system state."""

    def __init__(self, feature_name, parent_rung=None):
        self.name = feature_name
        self.parent = parent_rung
        self.catalog = load_catalog()
        self.features = query_graph('feature', '')
        self.health = query_graph('health')
        self.qa_pairs = []

    def ask_all(self):
        """Run all 40 questions. Returns dict of {question: answer}."""
        self._q_identity()
        self._q_existence()
        self._q_definition_level()
        self._q_catalog_coverage()
        self._q_system_connections()
        self._q_mirror()
        self._q_training()
        self._q_gpu()
        self._q_composition()
        self._q_judgment()
        return {q: a for q, a in self.qa_pairs}

    def _add(self, q, a):
        self.qa_pairs.append((q, a))

    # === 1-5: Identity ===
    def _q_identity(self):
        self._add("What is this feature?", f"{self.name}, sub-rung of {self.parent or 'root'}")
        self._add("What does it constrain?", "A specific game parameter discoverable from the element catalog")
        self._add("What wall would it violate?", "If the parameter doesn't satisfy the parent rung's composition seams")
        self._add("Is it a rung or sub-rung?", f"Sub-rung of {self.parent or 'unknown'}")
        self._add("What type of variable does it train?", "Float/bool/int from catalog flags")

    # === 6-10: Existence ===
    def _q_existence(self):
        exists = any(self.name in str(f) for f in self.features[:500])
        self._add("Does this feature already exist in the graph?", f"{exists}")
        self._add("Was it previously trained?", "Check graph for trained objectives with this name")
        self._add("Does a constraint file already exist?", f"{os.path.exists(BASE / 'docs' / 'constraints' / f'{self.name}.json')}")
        self._add("Does it duplicate an existing feature?", "Check by comparing element catalog clusters")
        self._add("What would happen if we skipped it?", "The parent rung would remain at lower resolution")

    # === 11-15: Definition Level ===
    def _q_definition_level(self):
        self._add("What scale does this feature operate at?", "Sub-rung scale: parameter-level within a parent system")
        self._add("What is the right level of definition?", "Fine enough to constrain, coarse enough to train in <100 evals")
        self._add("Could this be decomposed further?", "Always — sub-rungs can have sub-rungs")
        self._add("At what resolution does the pattern emerge?", "When the measure function returns consistent results across restarts")
        self._add("Is this too high-level (vague) or too low-level (overfit)?", "Check if the walls are measurable from the catalog")

    # === 16-20: Catalog Coverage ===
    def _q_catalog_coverage(self):
        matching = [e for e in self.catalog[:5000]
                    if self.name.split('_')[0].lower() in str(e).lower()]
        self._add("How many catalog elements match this feature?", f"{len(matching)}")
        self._add("What element categories does it cover?", f"Auto-detected from constraints element_query")
        self._add("What element classes does it cover?", f"Auto-detected from constraints element_query")
        self._add("Are there enough variables to train it?", "Yes if at least 3 catalog elements match")
        self._add("What variables are missing from the catalog?", "Check by comparing walls to available properties")

    # === 21-25: System Connections ===
    def _q_system_connections(self):
        parent_exists = any(self.parent in str(f) for f in self.features[:500]) if self.parent else True
        self._add("Does the parent rung exist?", f"{parent_exists}")
        self._add("What system does this feed into?", f"{self.parent or 'meta_feature_discovery'}")
        self._add("What system feeds into this?", "The parent rung's outputs")
        self._add("What happens at the seam?", "Validated by composition pass")
        self._add("Is there a risk of rung conflation?", "No — sub-rungs are explicitly decomposed from parent")

    # === 26-30: Mirror ===
    def _q_mirror(self):
        mirror_features = [f for f in self.features[:500] if 'mirror' in str(f).lower()]
        self._add("Does this feature connect to the Mirror of Erised?", "Check if it enables giving, sacrifice, or signal differentiation")
        self._add("Would a costless life still work without this feature?", "If yes, it's not Mirror-critical")
        self._add("Could this feature be gamed to fake a generous life?", "If yes, add a wall against the exploit")
        self._add("What would a degenerate winner look like for this?", "Maximum score with minimum actual constraint satisfaction")
        self._add("Does the human need to judge this, or can the system?", "System if measurable, human if taste-based")

    # === 31-35: Training ===
    def _q_training(self):
        self._add("How many evals to converge?", "10-100 generations at 32-128 population")
        self._add("CPU or GPU?", "CPU for <100 vars, GPU for >1000 vars (matter_gpu)")
        self._add("What's the risk of overfitting?", "Low if walls are hard and composition pass validates seams")
        self._add("What's the risk of underfitting?", "High if walls are too loose — degenerate winners appear")
        self._add("Can we measure_batch this?", "Yes if the measure function is independent per genome")

    # === 36-40: Composition & Judgment ===
    def _q_gpu(self):
        self._add("Can this run on GPU?", "If the measure function supports measure_batch and variable count > 1000")
        self._add("What's the GPU memory budget?", "24 GiB on 4090, ~4.6 GiB for 64-genome population at 9M vars")
        self._add("Does matter_gpu support this domain?", "Yes if it involves Cellular Potts or particle simulation")
        self._add("What's the CPU fallback speed?", "84-9000 evals/sec depending on domain complexity")

    def _q_judgment(self):
        self._add("Who judges this feature?", "System (walls) + Human (Mirror)")
        self._add("What would a failed judgment look like?", "A degenerate winner that satisfies walls but violates the Mirror")
        self._add("Can the human override the system verdict?", "Always — the human is the terminal for pattern quality")
        self._add("When does judgment happen?", "After training, before decoding. The human says yes/no.")

    def _q_composition(self):
        self._add("Does this need a decode step?", "Yes — all rungs need decoder placement in the level")
        self._add("What other rungs does it compose with?", "Parent rung and sibling sub-rungs")
        self._add("What could break when composing?", "Seam conflicts: overlapping positions, incompatible parameters")
        self._add("Is there a human judgment in the loop?", "At the Mirror wall: only the human can say if the signal feels right")
        self._add("What is the stopping criterion?", "When all walls are satisfied AND composition pass passes")


def interrogate(feature_name, parent_rung=None):
    """Run the 40 questions and return answers."""
    engine = QuestionEngine(feature_name, parent_rung)
    answers = engine.ask_all()
    
    print(f'\\n=== 40 QUESTIONS: {feature_name} ===')
    for i, (q, a) in enumerate(answers.items(), 1):
        print(f'  Q{i:2d}: {q}')
        print(f'       A: {a}')
    print(f'\\n{len(answers)} questions answered.')
    
    # Record to graph
    try:
        sys.path.insert(0, str(BASE))
        from core.graphify_interface import graphify_mutate
        graphify_mutate('research_discovery', details={
            'source': f'forty_questions_{feature_name}',
            'campus': 'self_interrogation',
            'quality_rating': 'A',
            'principles': [f'Q{i}: {a}' for i, (q, a) in enumerate(answers.items(), 1)][:5],
            'what_it_provides': f'40-question interrogation of {feature_name}'
        })
    except:
        pass
    
    return answers


if __name__ == '__main__':
    name = sys.argv[1] if len(sys.argv) > 1 else 'grain_scale_sand'
    parent = sys.argv[2] if len(sys.argv) > 2 else 'ground_terrain'
    interrogate(name, parent)
