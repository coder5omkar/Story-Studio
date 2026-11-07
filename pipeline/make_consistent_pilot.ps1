$ErrorActionPreference = "Stop"
$env:PYTHONIOENCODING = "utf-8"

$py = "D:\AI_Story_Channel\OpenMontage\.venv\Scripts\python.exe"
$project = "D:\AI_Story_Channel\projects\pilot_001"

Write-Host "Generating 30 scenes with IPAdapter face lock..."
& $py "D:\AI_Story_Channel\pipeline\images.py" --engine faceid --out-dir images_consistent --force

Write-Host "Re-rendering the pilot with the consistent images..."
& $py "D:\AI_Story_Channel\pipeline\assemble.py" --images-dir "$project\images_consistent" --out-name pilot_consistent.mp4

Write-Host "Done: $project\video\pilot_consistent.mp4"
