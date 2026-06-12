#!/bin/bash
# mark-pending.command
# 双击运行，将拖入的 md 文件标记为 ⬜ **待分析**
# 支持多个文件，拖入后按回车开始处理，处理完可继续拖入

DIR=$(cd "$(dirname "$0")" && pwd)

while true; do
    echo "请将标记为 ⬜ **待分析** 的 md 文件拖入此窗口（支持多个，空格分隔），然后按回车："
    read -r input

    success=0
    fail=0
    for raw_file in $input; do
        file=$(echo "$raw_file" | sed 's/^ *//;s/ *$//' | sed 's/^"//;s/"$//' | sed "s/^'//;s/'$//")
        if [ ! -f "$file" ]; then
            echo "❌ 文件不存在: $file"
            fail=$((fail + 1))
            continue
        fi
        if "$DIR/mark.sh" pending "$file" 2>/dev/null; then
            echo "✅ 成功: $file"
            success=$((success + 1))
        else
            echo "❌ 失败: $file"
            fail=$((fail + 1))
        fi
    done

    echo "--- 完成: $success 个成功, $fail 个失败 ---"
    echo ""
done
