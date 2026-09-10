"""Record the selected eye's capability and one owned engine-window observation."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    parser.add_argument('--image', required=True)
    args = parser.parse_args()
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=False)
    root = Path(__file__).resolve().parents[3]
    image = Path(args.image).resolve(strict=True)
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONIOENCODING='utf-8')
    tests = subprocess.run([sys.executable, '-m', 'unittest',
                            'tools.test_dyad_model_policy', '-v'], cwd=root,
                           env=env, capture_output=True, text=True, encoding='utf-8')
    (output / 'cpu_stdout.txt').write_text(tests.stdout, encoding='utf-8')
    (output / 'cpu_stderr.txt').write_text(tests.stderr, encoding='utf-8')
    if tests.returncode:
        return tests.returncode
    sys.path.insert(0, str(root / 'ChimeraEngine'))
    import senses
    source_paths = ['ChimeraEngine/senses.py', 'ChimeraEngine/dyad_model_policy.json']
    def hashes():
        return {name: hashlib.sha256((root / name).read_bytes()).hexdigest()
                for name in source_paths}
    before = hashes()
    original_gateway = senses._lm_gateway
    calls = []
    def recording_gateway():
        gateway = original_gateway()
        original_open = gateway.lm_urlopen
        def recorded_open(request, *positional, **kwargs):
            number = len(calls)
            calls.append(number)
            (output / f'request_{number}.json').write_bytes(request.data)
            # Inference waits are unbounded under the standing DYAD protocol.
            # The metadata readiness probe retains its finite transport timeout.
            kwargs['timeout'] = None
            response = original_open(request, *positional, **kwargs)
            try:
                raw = response.read()
                (output / f'response_{number}.json').write_bytes(raw)
            finally:
                close = getattr(response, 'close', None)
                if close is not None:
                    close()
            return io.BytesIO(raw)
        gateway.lm_urlopen = recorded_open
        return gateway
    senses._lm_gateway = recording_gateway
    result = {'source_sha256_before': before, 'image_path': str(image),
              'image_sha256': hashlib.sha256(image.read_bytes()).hexdigest(),
              'cpu_exit': tests.returncode, 'inference_timeout': None}
    try:
        result['can_see'] = senses.can_see()
        print('can_see:', result['can_see'], flush=True)
        if not result['can_see'][0]:
            return 1
        prompt = (
            'This is an actual captured client area of Chimera, a C++/Vulkan engine, '
            'before a shutdown regression test. You see one image and have no repository '
            'or prior conversation context. Independent logs test request cancellation '
            'and process exit; this picture alone cannot prove those events or physics. '
            'Previous capture attempts were rejected because another window obscured '
            'the target; this image used verified target client bounds. '
            'Do not infer hidden contents from expected identity. Answer numbered questions: '
            '1. What application and visible scene contents can you actually identify? '
            '2. What text, layout or rendering problems are visible, and where? '
            '3. Is there visible evidence of an error dialog or a different application? '
            'State uncertainty. 4. What is the single most important visible issue? '
            '5. Which claims about shutdown, motion or numerical physics cannot be '
            'established from this still image?'
        )
        (output / 'prompt.txt').write_text(prompt, encoding='utf-8')
        report = senses.watch_one(str(image), prompt)
        result.update(report=report, served_model=senses._last_served_model(),
                      finish_reason=senses.last_finish_reason())
        print('served:', result['served_model'], 'finish:', result['finish_reason'], flush=True)
        return 0 if (report and result['served_model'] == 'qwen3.8-27b-nvfp4-mtp'
                     and result['finish_reason'] == 'stop' and before == hashes()) else 1
    except Exception as exc:
        result['error'] = f'{type(exc).__name__}: {exc}'
        raise
    finally:
        result['source_sha256_after'] = hashes()
        (output / 'result.json').write_text(json.dumps(result, indent=2), encoding='utf-8')


if __name__ == '__main__':
    raise SystemExit(main())
