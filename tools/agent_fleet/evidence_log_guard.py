"""evidence_log_guard.py -- the *.log evidence-trap WARNING gate (F1).

THE TRAP (hit twice in wave 3 -- orient + engine lanes). A worker cites RAW
.log run outputs next to committed evidence; the repo-wide `*.log` gitignore
rule (.gitignore line 13) silently excludes those files from the commit. The
evidence commit lands, the cited raw output never existed in history, and
every later reader of the record hits a dead reference.

WHAT THIS IS. A pre-commit guard that WARNS -- it never blocks. When a commit
stages added files under docs/evidence/ while ignored-and-untracked *.log
files sit in the same directory (the trap signature), it names the files and
the two remedies (git add -f, or rename/copy the raw output to a committed
format) and exits 0 either way. A warning is visibility; the operator decides.

WIRING (per the repo's own hook convention, inspected before this existed):
.githooks/pre-commit is the repo-committed hook (enabled by
`git config core.hooksPath .githooks`); every gate there is an
existence-guarded stanza delegating to a script run from the repo root, with
a WHY comment. This script follows that shape (`--staged` mode) and its
stanza is warn-only by construction: the script exits 0 on every checked
path AND on internal error, so it cannot set the hook's fail flag. No
existing gate is weakened, removed, or bypassed.

Usage:  python tools/agent_fleet/evidence_log_guard.py --staged
"""
import argparse
import subprocess
import sys

EVIDENCE_PREFIX = 'docs/evidence/'
LOG_SUFFIX = '.log'


def git(repo, *args):
    """Run a git command in repo; raise with stderr on failure."""
    proc = subprocess.run(['git', '-C', str(repo), *args],
                          capture_output=True, text=True, encoding='utf-8')
    if proc.returncode != 0:
        raise RuntimeError('git %s failed: %s' % (' '.join(args),
                                                  proc.stderr.strip()))
    return proc.stdout


def staged_evidence_adds(repo):
    """Staged ADDED/copied paths under docs/evidence/ (A/C/A|M/R-letter adds).

    Only the add filters are the trap: a modified (M) file was already
    tracked, so its commit already survived history once.
    """
    out = git(repo, 'diff', '--cached', '--name-only', '--diff-filter=ACR',
              '--', EVIDENCE_PREFIX)
    return [line for line in out.splitlines() if line]


def ignored_logs_in(repo, directory):
    """Ignored-and-untracked *.log files under directory (the silent vanish)."""
    out = git(repo, 'ls-files', '--others', '--ignored', '--exclude-standard',
              '--', directory)
    return [line.replace('\\', '/') for line in out.splitlines()
            if line.lower().endswith(LOG_SUFFIX)]


def trap_signature(repo):
    """[(evidence_dir, [ignored *.log siblings...])] for every hit, else []."""
    hits = []
    seen_dirs = set()
    for path in staged_evidence_adds(repo):
        directory = path.rsplit('/', 1)[0] if '/' in path else '.'
        if directory in seen_dirs:
            continue
        seen_dirs.add(directory)
        logs = ignored_logs_in(repo, directory)
        if logs:
            hits.append((directory, logs))
    return hits


def warn(repo):
    """Print the named warning for each trap hit. ALWAYS exits 0."""
    try:
        hits = trap_signature(repo)
    except Exception as exc:  # a crashed guard must never block a commit
        print('[evidence-log-guard] WARNING: guard could not run '
              '(non-blocking): %s' % exc)
        return 0
    for directory, logs in hits:
        print('[evidence-log-guard] WARNING (not blocking): staged evidence '
              'in %s cites work whose RAW *.log files are ignored-and-'
              'untracked -- they will silently vanish behind the *.log '
              'gitignore rule:' % directory)
        for log in logs:
            print('  vanished: %s' % log)
        print('  remedy 1: git add -f %s/*.log   (commit the raw output)'
              % directory)
        print('  remedy 2: copy/rename the raw output to a committed '
              'format (*.txt) and cite that')
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--staged', action='store_true',
                        help='inspect the staged index (hook convention)')
    parser.add_argument('--repo', default='.',
                        help='repository root (defaults to cwd, as the hook)')
    args = parser.parse_args(argv)
    return warn(args.repo)


if __name__ == '__main__':
    sys.exit(main())
