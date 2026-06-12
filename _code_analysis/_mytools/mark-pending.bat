@echo off
chcp 65001 >nul
title mark-pending — 重置为 ⬜ 待分析
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
        REM 用 PowerShell 替换第一行：✅ **已分析** (含时间戳) → ⬜ **待分析**
        powershell -NoProfile -Command ^
            "$lines = Get-Content '%%~f';" ^
            "$lines[0] = $lines[0] -replace '^✅ \*\*已分析\*\*( -- .*)?$', '⬜ **待分析**';" ^
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
