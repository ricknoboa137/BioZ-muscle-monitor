param([int]$Passes = 30)
$ErrorActionPreference = "Stop"
$pcb    = "C:\Users\User\Documents\BioZ-muscle-monitor\pcb"
$kipy   = "C:\Program Files\KiCad\10.0\bin\python.exe"
$kicli  = "C:\Program Files\KiCad\10.0\bin\kicad-cli.exe"
# 2.2.4 blows the JVM stack (PolylineTrace.combine recursion) on this board even
# at -Xss1g and even with every pre-existing wire protected -- the recursion is on
# traces the router creates itself.  2.3.0 downloaded 2026-08-07 to replace it.
$fr     = "C:\Users\User\Documents\Agents\tools\freerouting\freerouting-2.3.0.jar"
$java   = (Get-ChildItem "C:\Users\User\Documents\Agents\tools\freerouting\jre25" -Recurse -Filter java.exe | Select-Object -First 1).FullName
$dsn    = "$pcb\board.dsn"
$ses    = "$pcb\board.ses"

Write-Host "== 0. strip degenerate/overlapping segments (Freerouting hangs on them) =="
& $kipy "$pcb\scripts\clean_tracks.py"
Write-Host "== 1. export DSN =="
& $kipy "$pcb\scripts\dsn_io.py" export $dsn
Write-Host "== 2. patch plane layers =="
& $kipy "$pcb\scripts\patch_dsn.py" $dsn
if ($LASTEXITCODE -ne 0) { throw "DSN plane patch failed - refusing to route" }
Write-Host "== 3. freerouting ($Passes passes) =="
# -Xss1g: the pre-existing hand-routed escape is made of many short collinear
# segments and Freerouting's PolylineTrace.combine() recurses once per segment.
# On the default 1 MB stack it throws StackOverflowError while loading the DSN.
& $java -Xss1g -Xmx4g -jar $fr --gui.enabled=false -de $dsn -do $ses -mp $Passes
Write-Host "== 4. import SES =="
& $kipy "$pcb\scripts\dsn_io.py" import $ses
Write-Host "== 4b. restore laser microvias (Specctra loses the via type) =="
& $kipy "$pcb\scripts\restore_microvias.py"
Write-Host "== 4c. put the board back on its origin (SES import translates it) =="
& $kipy "$pcb\scripts\fix_origin.py"
Write-Host "== 5. DRC =="
& $kicli pcb drc --format json --output "$pcb\drc.json" --severity-error "$pcb\BioZ-Muscle-Monitor.kicad_pcb"
& $kipy "$pcb\scripts\layer_census.py"
