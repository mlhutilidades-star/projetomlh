$env:PYTHONPATH = "$PSScriptRoot\..";
Set-Location "$PSScriptRoot\.."
python -m alembic upgrade head
