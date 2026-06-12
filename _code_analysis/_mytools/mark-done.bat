@echo off
chcp 65001 >nul
title mark-done — 标记为 ✅ 已分析
cd /d "%~dp0"
setlocal enabledelayedexpansion

:loop
echo 请将 md 文件拖入此窗口（支持多个），然后按回车：
echo 或直接按回车退出。
set "input="
set /p "input="
if "%input%"=="" exit /b

set success=0
set fail=0

for %%f in (%input%) do (
    if not exist "%%~f" (
        echo ❌ 文件不存在: %%~f
        set /a fail+=1
    ) else (
        REM 用 PowerShell 替换第一行：⬜ **待分析** → ✅ **已分析** -- 北京时间
        powershell -NoProfile -Command ^
            "$now = [DateTimeOffset]::UtcNow.ToOffset([TimeSpan]::FromHours(8)).ToString('yyyy-MM-dd HH:mm');" ^
            "$lines = Get-Content '%%~f';" ^
            "$lines[0] = $lines[0] -replace '^⬜ \*\*待分析\*\*.*', \"✅ **已分析** -- $now\";" ^
            "$lines | Set-Content '%%~f' -Encoding UTF8;"
        if !errorlevel! equ 0 (
            echo ✅ 成功: %%~f
            set /a success+=1
        ) else (
            echo ❌ 失败: %%~f
            set /a fail+=1
        )
    )
)

echo --- 完成: !success! 个成功, !fail! 个失败 ---
echo.
goto loop
