#!/bin/bash
# 用法：
#   mark.sh pending <md文件>    — 设为 ⬜ **待分析**
#   mark.sh done    <md文件>    — 设为 ✅ **已分析** -- 北京时间
#
# 也支持被 mark-done.command / mark-pending.command 调用（自动识别文件名）

# — 识别命令来源 ----------------------------------------------------------

cmd=$(basename "$0")
if [ "$cmd" = "mark-pending.command" ]; then
    action="pending"
elif [ "$cmd" = "mark-done.command" ]; then
    action="done"
else
    action="$1"
    shift
fi

# — 参数检查 ------------------------------------------------------------

file="$1"
if [ -z "$file" ] || [ ! -f "$file" ]; then
    echo "用法:"
    echo "  mark.sh pending <md文件>"
    echo "  mark.sh done    <md文件>"
    exit 1
fi

# — 执行替换 ------------------------------------------------------------

case "$action" in
    pending)
        # ✅ **已分析** (含可选时间戳) → ⬜ **待分析**
        perl -i -pe 's{^✅ \*\*已分析\*\*( -- .*)?$}{⬜ **待分析**} if $. == 1' "$file"
        echo '⬜ 已重置为 待分析'
        ;;
    done)
        # ⬜ **待分析** → ✅ **已分析** -- 北京时间
        now=$(TZ='Asia/Shanghai' date '+%Y-%m-%d %H:%M')
        perl -i -pe "s{^⬜ \*\*待分析\*\*.*}{✅ **已分析** -- ${now}} if $. == 1" "$file"
        echo "✅ 已标记为 已分析（${now}）"
        ;;
    *)
        echo "未知命令: $action (请用 pending 或 done)"
        exit 1
        ;;
esac
