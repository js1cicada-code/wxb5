#!/bin/bash

PROJECT_DIR="/Users/bluekyo/Documents/wxingbaoh5"
LAUNCHD_DIR="$HOME/Library/LaunchAgents"

mkdir -p "$LAUNCHD_DIR"

create_plist() {
    local name=$1
    local interval=$2
    local script=$3
    
    cat > "$LAUNCHD_DIR/com.lottery.$name.plist" << PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.lottery.$name</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>$PROJECT_DIR/$script</string>
    </array>
    <key>StartInterval</key>
    <integer>$interval</integer>
    <key>StandardOutPath</key>
    <string>$PROJECT_DIR/logs/launchd_$name.log</string>
    <key>StandardErrorPath</key>
    <string>$PROJECT_DIR/logs/launchd_$name.err</string>
    <key>WorkingDirectory</key>
    <string>$PROJECT_DIR</string>
</dict>
</plist>
PLIST
    
    echo "已创建: $LAUNCHD_DIR/com.lottery.$name.plist"
}

echo "创建 Launchd 服务..."
echo ""

create_plist "fast" 300 "scheduled_update.py"
create_plist "medium" 600 "scheduled_update.py"
create_plist "slow" 1800 "scheduled_update.py"

echo ""
echo "加载服务..."
launchctl unload "$LAUNCHD_DIR/com.lottery.fast.plist" 2>/dev/null
launchctl unload "$LAUNCHD_DIR/com.lottery.medium.plist" 2>/dev/null
launchctl unload "$LAUNCHD_DIR/com.lottery.slow.plist" 2>/dev/null

launchctl load "$LAUNCHD_DIR/com.lottery.fast.plist"
launchctl load "$LAUNCHD_DIR/com.lottery.medium.plist"
launchctl load "$LAUNCHD_DIR/com.lottery.slow.plist"

echo ""
echo "服务状态:"
launchctl list | grep lottery

echo ""
echo "==========================================="
echo "Launchd 服务已创建并启动！"
echo ""
echo "管理命令:"
echo "  查看状态: launchctl list | grep lottery"
echo "  停止服务: launchctl unload ~/Library/LaunchAgents/com.lottery.*.plist"
echo "  启动服务: launchctl load ~/Library/LaunchAgents/com.lottery.*.plist"
echo "==========================================="