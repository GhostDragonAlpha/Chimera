$ErrorActionPreference = 'Continue'
& 'E:\PythonChimera\.venv-hy3d\Scripts\python.exe' -B -m unittest discover -s 'tools/science_funnel/tests' 1> 'E:\ChimeraWork\paper-inertia-20260918\tools\creature_graph\validation\batch_paper_inertia_20260918\funnel_suite_stdout.log' 2> 'E:\ChimeraWork\paper-inertia-20260918\tools\creature_graph\validation\batch_paper_inertia_20260918\funnel_suite_stderr.log'
$LASTEXITCODE | Set-Content -Path 'E:\ChimeraWork\paper-inertia-20260918\tools\creature_graph\validation\batch_paper_inertia_20260918\funnel_suite_done.txt'
