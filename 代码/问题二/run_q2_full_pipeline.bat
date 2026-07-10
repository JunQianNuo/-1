@echo off
setlocal

REM Place this BAT and run_q2_full_pipeline.py in:
REM D:\知识库\数学建模\第一次\代码\问题二

cd /d "%~dp0"

python run_q2_full_pipeline.py ^
  --anchors 400,800,1200,1600 ^
  --output-root results_full_pipeline ^
  --integer-window 60 ^
  --confirmation-lookback 3 ^
  --certificate-forward-limit 20

set EXITCODE=%ERRORLEVEL%

echo.
echo Pipeline exit code: %EXITCODE%
echo Main report:
echo   results_full_pipeline\q2_full_pipeline_result.json
echo Run table:
echo   results_full_pipeline\q2_full_pipeline_runs.csv

endlocal
exit /b %EXITCODE%
