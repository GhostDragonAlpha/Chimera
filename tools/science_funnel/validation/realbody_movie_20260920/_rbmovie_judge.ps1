Set-Location E:\ChimeraWork\rbmovie-agent\tools\science_funnel\validation\realbody_movie_20260920
python rbmovie_judge.py --frames E:\ChimeraWork\rbmovie-scratch\frames --capture-record capture_record.json --n 12 1> E:\ChimeraWork\rbmovie-scratch\logs\judge_log.txt 2>&1
exit $LASTEXITCODE
