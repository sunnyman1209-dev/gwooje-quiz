# 사용: run_trans.ps1 -Batches g1,g2,... [-Parallel 3] [-Model auto]
# 묶음마다 Cursor CLI를 돌려 quiz/work/trans/<묶음>.jsonl 을 만든다. 기록은 quiz/work/logs/<묶음>.log
param([string[]]$Batches, [int]$Parallel = 3, [string]$Model = 'auto', [int]$TimeoutSec = 3600)
$H = Split-Path (Split-Path $PSScriptRoot)
$agent = Join-Path $env:LOCALAPPDATA 'cursor-agent\agent.cmd'
$logs = Join-Path $H 'quiz\work\logs'
New-Item -ItemType Directory -Force $logs | Out-Null
$queue = [System.Collections.Queue]::new(); $Batches | ForEach-Object { $queue.Enqueue($_) }
$running = @{}
while ($queue.Count -gt 0 -or $running.Count -gt 0) {
    while ($running.Count -lt $Parallel -and $queue.Count -gt 0) {
        $b = $queue.Dequeue()
        $prompt = "Read the file quiz/work/packs/$b.md in the current workspace and follow its instructions exactly. Write only quiz/work/trans/$b.jsonl. Answer in Korean."
        $running[$b] = Start-Job -ScriptBlock {
            param($cmd, $model, $p, $wd, $log)
            Set-Location $wd
            [Console]::OutputEncoding = [Text.Encoding]::UTF8
            & $cmd -p --trust --force --output-format text --model $model $p 2>&1 | ForEach-Object { "$_" } | Out-File $log -Encoding utf8
        } -ArgumentList $agent, $Model, $prompt, $H, (Join-Path $logs "$b.log")
        Write-Output "$(Get-Date -Format HH:mm) 시작 $b"
    }
    Start-Sleep 15
    foreach ($b in @($running.Keys)) {
        $j = $running[$b]
        $age = ((Get-Date) - $j.PSBeginTime).TotalSeconds
        if ($j.State -ne 'Running' -or $age -gt $TimeoutSec) {
            if ($j.State -eq 'Running') { Stop-Job $j; Write-Output "$(Get-Date -Format HH:mm) 시간초과 $b" }
            Remove-Job $j -Force; $running.Remove($b)
            $f = Join-Path $H "quiz\work\trans\$b.jsonl"
            $n = if (Test-Path $f) { (Get-Content $f -Encoding utf8 | Where-Object { $_.Trim() }).Count } else { 0 }
            Write-Output "$(Get-Date -Format HH:mm) 끝 $b ($n 줄)"
        }
    }
}
Write-Output "전체 완료"

