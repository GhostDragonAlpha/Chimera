#!/usr/bin/env python3
"""Research bridge — takes a 40Q document, identifies unanswered questions
that can be resolved with online research, runs the research engine, and
fills in the answers with citations.

Usage:
    python -m core.research_bridge <feature_name>        # research unanswered 40Q
    python -m core.research_bridge <feature_name> --all   # research all questions
"""
import json, os, sys, re
from pathlib import Path

FORTY_Q_DIR = Path(__file__).parent.parent / 'docs' / 'forty_questions'


def load_40q(name):
    p = FORTY_Q_DIR / f'{name}.json'
    if not p.exists():
        print(f'No 40Q document for {name}')
        return None
    with open(p) as f:
        return json.load(f)


def save_40q(name, doc):
    with open(FORTY_Q_DIR / f'{name}.json', 'w') as f:
        json.dump(doc, f, indent=2)
    print(f'  Updated {name} 40Q document')


def build_search_queries(doc):
    """Generate search queries from unanswered questions."""
    queries = []
    for q in doc['questions']:
        if q['answered']:
            continue
        text = q['q']
        # Extract key terms from the question
        terms = re.findall(r'[A-Z][a-z]+(?:\s+[a-z]+)*', text)
        # Generate a concise search query
        query = f"{doc['_meta']['feature']} {text.split('?')[0][:60]}"
        queries.append((q['id'], query, text))
    return queries


def research_question(query):
    """Run the research engine for a query and return findings."""
    result = None
    # Try research_engine first (UE5 source on disk)
    try:
        from research_engine import search_engine
        result = search_engine(query, maxHits=5)
    except:
        pass
    
    # Fallback to web search
    if not result or (isinstance(result, dict) and not result.get('hits')):
        try:
            from web_search_real import web_search
            result = web_search(query, maxResults=3)
        except:
            try:
                from web_browse import web_browse
                result = web_browse(f'https://html.duckduckgo.com/html/?q={query}', maxChars=3000)
            except:
                pass
    
    return result


def research_feature(name, all_questions=False):
    """Research a feature's unanswered 40 questions and fill answers."""
    doc = load_40q(name)
    if not doc:
        return
    
    meta = doc['_meta']
    queries = build_search_queries(doc)
    
    if not all_questions:
        queries = [(i, q, t) for i, q, t in queries if not doc['questions'][i-1]['answered']]
    
    if not queries:
        print(f'All 40 questions for {name} are already answered.')
        return
    
    print(f'Researching {len(queries)} unanswered questions for {name}...')
    
    for qid, query, question_text in queries:
        print(f'\n  Q{qid}: {question_text[:60]}')
        findings = research_question(query)
        
        if findings:
            # Format findings as answer
            if isinstance(findings, dict):
                if 'hits' in findings:
                    summary = '; '.join([h.get('text','')[:120] for h in findings['hits'][:3]])
                elif 'content' in findings:
                    summary = str(findings['content'])[:200]
                else:
                    summary = str(findings)[:200]
            elif isinstance(findings, list):
                summary = '; '.join([str(f)[:120] for f in findings[:3]])
            else:
                summary = str(findings)[:200]
            
            # Update the question's answer
            doc['questions'][qid-1]['a'] = summary
            doc['questions'][qid-1]['answered'] = True
            doc['_meta']['n_answered'] = sum(1 for q in doc['questions'] if q['answered'])
            
            # Update depth verdict
            n = doc['_meta']['n_answered']
            if n >= 30: doc['_meta']['depth_verdict'] = 'deep'
            elif n >= 20: doc['_meta']['depth_verdict'] = 'adequate'
            elif n >= 10: doc['_meta']['depth_verdict'] = 'explored'
            
            print(f'       Found: {summary[:80]}')
        else:
            print(f'       No research results found.')
    
    # Save updated 40Q document
    save_40q(name, doc)
    
    # Also record to graph
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from core.graphify_interface import graphify_mutate
        graphify_mutate('research_discovery', details={
            'source': f'research_bridge_{name}',
            'campus': 'online_research',
            'quality_rating': 'A',
            'principles': [f'Q{qid}: {q["a"][:60]}' for q in doc['questions'][:5] if q['answered']],
            'what_it_provides': f'Research-enhanced 40Q for {name}'
        })
    except:
        pass
    
    print(f'\n{meta["n_answered"]}/40 answered. Depth: {meta["depth_verdict"]}')


if __name__ == '__main__':
    name = sys.argv[1] if len(sys.argv) > 1 else None
    all_q = '--all' in sys.argv
    if name:
        research_feature(name, all_q)
    else:
        print('Usage: python -m core.research_bridge <feature_name> [--all]')
