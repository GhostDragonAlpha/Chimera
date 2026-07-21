#!/usr/bin/env python3
"""40-question document generator — generates and saves 40 questions per feature.
Questions are saved as docs/forty_questions/<feature_name>.json and persist forever.
They define the scope, depth, and Mirror connection for that feature.
Future iterations read them to know if the feature is complete.
"""
import json, os, sys
from pathlib import Path

QUESTIONS_DIR = Path(__file__).parent.parent / 'docs' / 'forty_questions'


def generate(feature_name, parent_rung=None, walls=None):
    """Generate 40 questions for a feature, save to docs/forty_questions/<name>.json.
    Questions are generated from first principles — not from system state — so they
    define the feature's potential regardless of whether it exists yet.
    """
    QUESTIONS_DIR.mkdir(parents=True, exist_ok=True)
    
    questions = []
    
    # 1-5: Identity
    questions.append(("What IS this feature in one sentence?", f"{feature_name}"))
    questions.append(("What wider system does it belong to?", f"{parent_rung or 'root'}"))
    questions.append(("What would break if this feature didn't exist?", ""))
    questions.append(("What existing feature does this most resemble?", ""))
    questions.append(("Is this a rung, a sub-rung, or a parameter?", "sub-rung"))
    
    # 6-10: Constraint
    questions.append(("What physical constraint does it encode?", ""))
    questions.append(("What is the ONE measurement that proves it works?", ""))
    questions.append(("What wall must it never violate?", ""))
    questions.append(("What would a degenerate winner look like?", ""))
    questions.append(("How would we know if the constraint is too loose?", ""))
    
    # 11-15: Scale
    questions.append(("At what scale does this feature operate?", ""))
    questions.append(("What is the right definition level for this scale?", ""))
    questions.append(("Could this be decomposed further? Into what?", ""))
    questions.append(("At what resolution does the pattern emerge?", ""))
    questions.append(("What would 'deep enough' look like for this feature?", ""))
    
    # 16-20: Catalog
    questions.append(("What element catalog variables does this train?", ""))
    questions.append(("How many relevant elements exist in the catalog?", ""))
    questions.append(("Are there enough variables to train meaningfully?", ""))
    questions.append(("What variables are MISSING from the catalog?", ""))
    questions.append(("Would training this require GPU acceleration?", ""))
    
    # 21-25: Mirror
    questions.append(("Does this feature connect to the Mirror of Erised?", ""))
    questions.append(("How directly does it serve the Mirror? (direct/enabling/orthogonal)", ""))
    questions.append(("Would a costless life still be meaningful without this feature?", ""))
    questions.append(("Could this feature be gamed to fake a generous life?", ""))
    questions.append(("What would this feature look like if it perfectly served the Mirror?", ""))
    
    # 26-30: Composition
    questions.append(("What other features does this compose with?", ""))
    questions.append(("What could break at the seam between this and its neighbors?", ""))
    questions.append(("Does this need a decoder step to place in the level?", ""))
    questions.append(("What would a failed composition look like?", ""))
    questions.append(("Does this feature need a human judgment or can the system verify it?", ""))
    
    # 31-35: Training
    questions.append(("How many generations to converge?", "10-100"))
    questions.append(("What population size is appropriate?", "32-128"))
    questions.append(("What's the risk of overfitting?", ""))
    questions.append(("What's the risk of underfitting?", ""))
    questions.append(("Does the existing trainer support this domain type?", ""))
    
    # 36-40: Depth
    questions.append(("Have we gone deep enough on this feature?", ""))
    questions.append(("What would the NEXT level of decomposition look like?", ""))
    questions.append(("If we stopped here, would the game feel complete?", ""))
    questions.append(("What is the human's expected emotional response to this feature?", ""))
    questions.append(("Does this feature exist because the Mirror demands it, or because it's technically interesting?", ""))
    
    doc = {
        '_meta': {
            'feature': feature_name,
            'parent': parent_rung,
            'walls': walls or [],
            'created': 'auto',
            'n_total': 40,
            'n_answered': 0,
            'depth_verdict': 'unexplored'
        },
        'questions': [{'id': i+1, 'q': q, 'a': '', 'answered': False} for i, (q, _) in enumerate(questions)]
    }
    
    path = QUESTIONS_DIR / f'{feature_name}.json'
    with open(path, 'w') as f:
        json.dump(doc, f, indent=2)
    
    print(f'40 questions saved to {path}')
    print(f'  Answered: {doc["_meta"]["n_answered"]}/{doc["_meta"]["n_total"]}')
    print(f'  Depth: {doc["_meta"]["depth_verdict"]}')
    return doc


def answer(feature_name, question_id, answer_text):
    """Fill in an answer for a specific question on an existing feature.
    Updates the depth_verdict based on how many questions are now answered."""
    path = QUESTIONS_DIR / f'{feature_name}.json'
    if not path.exists():
        print(f'No 40Q document for {feature_name}. Generate it first.')
        return
    
    with open(path) as f:
        doc = json.load(f)
    
    for q in doc['questions']:
        if q['id'] == question_id:
            q['a'] = answer_text
            q['answered'] = True
            break
    
    n_answered = sum(1 for q in doc['questions'] if q['answered'])
    doc['_meta']['n_answered'] = n_answered
    if n_answered >= 30:
        doc['_meta']['depth_verdict'] = 'deep'
    elif n_answered >= 20:
        doc['_meta']['depth_verdict'] = 'adequate'
    elif n_answered >= 10:
        doc['_meta']['depth_verdict'] = 'explored'
    else:
        doc['_meta']['depth_verdict'] = 'unexplored'
    
    with open(path, 'w') as f:
        json.dump(doc, f, indent=2)
    print(f'  Q{question_id} answered: {doc["_meta"]["depth_verdict"]} ({n_answered}/40)')


def check_depth(feature_name):
    """Read existing 40 questions for a feature and return depth assessment."""
    path = QUESTIONS_DIR / f'{feature_name}.json'
    if not path.exists():
        return {'exists': False, 'depth': 'unknown'}
    with open(path) as f:
        doc = json.load(f)
    answered = doc.get('n_answered', 0)
    total = doc.get('n_total', 40)
    return {
        'exists': True,
        'depth': 'deep' if answered >= 30 else ('adequate' if answered >= 20 else 'shallow'),
        'answered': answered,
        'total': total,
        'verdict': doc.get('depth_verdict', 'unknown')
    }


def show(feature_name):
    """Display the 40-question document for a feature."""
    path = QUESTIONS_DIR / f'{feature_name}.json'
    if not path.exists():
        print(f'No 40Q document for {feature_name}')
        return
    with open(path) as f:
        doc = json.load(f)
    meta = doc['_meta']
    print(f'=== {meta["feature"]} (parent: {meta["parent"]}) ===')
    print(f'Depth: {meta["depth_verdict"]} | Answered: {meta["n_answered"]}/{meta["n_total"]}')
    for q in doc['questions']:
        status = '[x]' if q['answered'] else '[ ]'
        a = f' → {q["a"][:60]}' if q['answered'] else ''
        print(f'  {status} Q{q["id"]:2d}: {q["q"][:60]}{a}')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python -m core.forty_questions generate <name> [parent]')
        print('       python -m core.forty_questions answer <name> <qid> <answer>')
        print('       python -m core.forty_questions show <name>')
        sys.exit(1)
    action = sys.argv[1]
    name = sys.argv[2] if len(sys.argv) > 2 else None
    if action == 'generate':
        parent = sys.argv[3] if len(sys.argv) > 3 else None
        generate(name, parent)
    elif action == 'answer':
        qid = int(sys.argv[3]) if len(sys.argv) > 3 else None
        answer_text = ' '.join(sys.argv[4:]) if len(sys.argv) > 4 else ''
        answer(name, qid, answer_text)
    elif action == 'show':
        show(name)
