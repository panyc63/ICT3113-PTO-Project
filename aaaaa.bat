@echo off
setlocal enabledelayedexpansion
set MODEL=llama3.2-3b
set PLAN=jmeter\test_plans\ticket-load-test3B.jmx

for %%P in ("52.44 104.89" "78.67 157.33" "160 320") do (
  for /f "tokens=1,2" %%a in (%%P) do (
    set DIR=jmeter\results\%MODEL%\%%a_%%b
    mkdir !DIR! 2>nul
    for %%N in (1 2 3) do (
      rem --- your reset policy and service log start go here ---
      del /q !DIR!\run%%N.jtl 2>nul
      call jmeter -n -t %PLAN% ^
        -l !DIR!\run%%N.jtl ^
        -j !DIR!\run%%N.jmeter.log ^
        -Jsample_variables=row,request_id ^
        -Jhost=localhost -Jport=8000 ^
        -Jpost_rate=%%a -Jsearch_rate=%%b
      rem --- copy this run's service log to !DIR!\run%%N.service.jsonl ---
    )
  )
)