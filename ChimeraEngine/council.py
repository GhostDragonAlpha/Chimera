"""
Council — dialectical Q&A engine for Chimera Engine.

The Council is the design layer: it asks questions about the system,
researches answers, and formulates design constraints.

In the Unreal Chimera, the Council uses LM Studio for two-brain
dialogue (fast model + deep model). In the standalone Chimera Engine,
it queries the particle simulation state and generates design questions.

Modes:
  - analyze: inspect current simulation state, surface surprises
  - question: generate design questions based on gaps
  - research: query the web for technical answers (optional)
"""

import json, time, subprocess
from dataclasses import dataclass, field


@dataclass
class Question:
    text: str
    category: str  # "design", "technical", "emergent"
    answer: str | None = None
    researched: bool = False
    timestamp: float = field(default_factory=time.time)


class Council:
    """
    Dialectical design council. Queries the system, surfaces questions.

    Usage:
        c = Council()
        questions = c.analyze(particle_data, pipe)
        for q in questions:
            print(q.text)
    """

    def __init__(self, fast_model: str = None, deep_model: str = None):
        self.fast_model = fast_model
        self.deep_model = deep_model
        self._history: list[Question] = []

    def analyze(self, particle_data, pipe) -> list[Question]:
        """Surface design questions from simulation state."""
        questions = []
        n = pipe._n if hasattr(pipe, '_n') else len(particle_data)
        NCOLS = 28; TYPE = 11; PROP0 = 12; PROP1 = 13

        # Count types
        type_counts = {}
        for i in range(n):
            t = int(particle_data[i, TYPE])
            type_counts[t] = type_counts.get(t, 0) + 1

        type_names = {0: "dust", 1: "sand", 2: "water", 3: "social",
                      4: "resource", 5: "atmosphere", 6: "shellmite", 7: "weapon_glint"}

        # Surprise: no atmosphere
        if type_counts.get(5, 0) < 100:
            questions.append(Question(
                "Should we increase atmosphere particle density for visual depth?",
                "design"))

        # Surprise: dust not accumulating
        dust_mask = particle_data[:n, TYPE] == 0
        if dust_mask.any():
            avg_accum = float(particle_data[:n][dust_mask, PROP0].mean())
            if avg_accum < 0.01:
                questions.append(Question(
                    f"Dust accumulation is near zero ({avg_accum:.4f}). "
                    "Is gravity too weak or accumulation_rate too low?",
                    "technical"))

        # Surprise: no social/resource particles
        if type_counts.get(3, 0) == 0 and type_counts.get(4, 0) == 0:
            questions.append(Question(
                "Social and resource particle types exist but none spawned. "
                "When should emergent NPC/trade behaviors activate?",
                "emergent"))

        # Surprise: uniform temperature
        if dust_mask.any():
            avg_temp = float(particle_data[:n][dust_mask, PROP1].mean())
            if abs(avg_temp - 20.0) < 0.1:
                questions.append(Question(
                    "Temperature is uniform across all particles. "
                    "Should different regions have different ambient temperatures?",
                    "emergent"))

        self._history.extend(questions)
        return questions

    def ask_lm(self, question: Question) -> str:
        """Query LM Studio for design guidance (if available)."""
        try:
            result = subprocess.run(
                ["python", "-c", f"""
import requests
r = requests.post('http://localhost:1234/v1/chat/completions',
    json={{"model":"local-model","messages":[{{"role":"user","content":"{question.text}"}}],"max_tokens":200}},
    timeout=10)
print(r.json()['choices'][0]['message']['content'])
"""],
                capture_output=True, text=True, timeout=15,
            )
            if result.returncode == 0:
                question.answer = result.stdout.strip()[:500]
                question.researched = True
                return question.answer
        except Exception:
            pass
        return "LM Studio not available."

    @property
    def open_questions(self) -> list[Question]:
        return [q for q in self._history if not q.researched]
