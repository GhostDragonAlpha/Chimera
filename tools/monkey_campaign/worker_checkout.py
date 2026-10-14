"""Provision pinned file packages; preserve already-owned legacy checkouts."""
from pathlib import Path
import json
import task_package as packages


def git(repo, *args):
    return packages.git(repo, *args).decode().strip()


def prepare(source, allocation):
    source = Path(source).resolve(strict=True)
    assignment = allocation.get('attempt') or allocation.get('review')
    if assignment is None:
        return None
    attempt = Path(assignment['workspace']).resolve()
    attempt.mkdir(parents=True, exist_ok=True)
    identity = dict(task_id=allocation['task_id'], assignment_id=assignment['id'], source=str(source))
    legacy = attempt/'checkout_identity.json'
    if legacy.exists():
        saved = json.loads(legacy.read_text())
        if any(saved.get(k) != v for k, v in identity.items()):
            raise ValueError('checkout_identity_mismatch_preserve_work')
        checkout = attempt/'checkout'
        if git(checkout, 'branch', '--show-current') != saved['branch']:
            raise ValueError('checkout_branch_changed_preserve_work')
        return {**saved, 'working_directory':str(checkout), 'state':'LEGACY_RESUMED',
                'git_checkout_created':False, 'legacy':True}
    if (attempt/'checkout').exists():
        raise ValueError('unrecorded_checkout_preserved_inspect_before_retry')
    package = attempt/'package'
    manifest = package/'package.json'
    if manifest.exists():
        saved = json.loads(manifest.read_text())
        if saved['source'] != str(source) or saved['task'] != identity['task_id'] or saved['owner'] != assignment['id']:
            raise ValueError('package_identity_mismatch_preserve_work')
        return {**identity, 'state':'RESUMED', 'package':str(package),
                'working_directory':str(package/'files'), 'base':saved['base'], 'git_checkout_created':False}
    if package.exists():
        raise ValueError('incomplete_package_preserved')
    # Never substitute the current working branch: it may belong to another agent.
    base = assignment.get('head_sha') or allocation.get('base_sha')
    if not base:
        branch = allocation.get('publication_branch') or allocation.get('checkout_branch')
        if not branch:
            raise ValueError('explicit_base_or_publication_branch_required')
        base = 'refs/remotes/origin/'+branch
    try:
        head = git(source, 'rev-parse', '--verify', base+'^{commit}')
    except ValueError as exc:
        raise ValueError('pinned_base_unavailable_refresh_named_ref_in_shared_repository: '+base) from exc
    brief = allocation.get('brief', {})
    path = brief.get('pr_destination', 'tools/monkey_campaign/contributions/'+allocation['task_id']).rstrip('/')
    packages.relpath(path)
    if not path.startswith('tools/monkey_campaign/contributions/'):
        raise ValueError('invalid_contribution_scope')
    reads = list(brief.get('package_reads', []))
    if allocation['task_id'].startswith('MAT2-M'):
        reads += ['tools/monkey_campaign/contributions/MAT2-M%02d'%n for n in range(1,8)]
    prepared = packages.create(source, head, package, assignment['id'], allocation['task_id'], reads, [path])
    return {**identity, **prepared, 'publication_branch':allocation.get('publication_branch'),
            'next_action':'Edit package/files only. Seal with task_package.py seal. Run CPU commands through task_package.py run. Submit sealed patch and hashes to the existing publication owner. Required preregistration commits must be published before experiments; a seal is not a Git commit.'}


def provision_output(source, out):
    """Only executable allocations provision; parking/ASK/coordination stay parked."""
    allocation = out.get('assignment', {})
    if allocation.get('state') not in ('ASSIGNED', 'RESUME_ATTEMPT', 'REVIEW_ASSIGNED'):
        return out
    try:
        prepared = prepare(source, allocation)
        if prepared:
            allocation['workspace_preparation'] = prepared
            allocation['checkout_ready'] = True
            out['working_directory'] = prepared['working_directory']
            if not prepared.get('legacy'):
                allocation['next_action'] = out['next_action'] = prepared.get('next_action',
                    'Resume package/files; seal and run through task_package.py; publication remains serialized.')
    except (ValueError, OSError) as exc:
        allocation['checkout_ready'] = False
        allocation['workspace_preparation'] = {'state':'BLOCKED', 'error':str(exc)}
        out['next_action'] = 'Preserve the existing assignment. Resolve workspace_preparation.error; do not create a clone or worktree as fallback.'
    return out
