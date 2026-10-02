"""Worker-intake hook for the operator's workspace retention policy."""
import importlib.util
import json
from pathlib import Path

TOOL = Path('E:/ChimeraWork/tools/workspace_lifecycle.py')


def augment(out, collect=True):
    policy = {
        'tool': str(TOOL),
        'instructions': 'E:/ChimeraWork/tools/WORKSPACE_LIFECYCLE.md',
        'required': 'New attempts use task_package.py file packages; no new clones or worktrees. '
                    'Worker startup returns the prepared directory. Run CPU commands through '
                    'task_package.py run so the runner preserves declared outputs and deletes scratch. '
                    'Read E:/PythonChimera/tools/monkey_campaign/NO_WORKTREES.md. '
                    'Existing checkout owners may finish safely and use the legacy release tool; '
                    'never release another agent or shared checkout.',
        'new_workspace_tool': 'E:/PythonChimera/tools/monkey_campaign/task_package.py',
        'new_workspace_instructions': 'E:/PythonChimera/tools/monkey_campaign/NO_WORKTREES.md',
    }
    try:
        spec = importlib.util.spec_from_file_location('chimera_workspace_lifecycle', TOOL)
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        lc = module.Lifecycle()
        policy['collection'] = lc.collect() if collect else 'read_only_check'
        owner = out.get('arrival_id')
        policy['your_workspaces'] = [r for f in lc.records()
                                    if (r := json.loads(f.read_text()))['owner'] == owner
                                    and r['state'] != 'COLLECTED']
    except Exception as exc:
        # Storage failure is visible and never becomes permission to delete.
        policy['error'] = str(exc)
    from runner_resources import profile
    policy['resource_profile'] = profile()
    out['workspace_lifecycle'] = policy
    return out
