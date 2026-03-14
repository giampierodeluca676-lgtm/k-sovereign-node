#!/bin/bash
clear
echo -e "\033[1;32m=== K-SOVEREIGN NODE ATTIVO ===\033[0m"

pkill -f "keygap_bot.py" > /dev/null 2>&1
pkill -f "127.0.0.1:8100" > /dev/null 2>&1
fuser -k 8100/tcp > /dev/null 2>&1
sleep 1

> output.log
python3 -u keygap_bot.py >> output.log 2>&1 &
tail -f output.log &
LOG_PID=$!

ssh -o ServerAliveInterval=60 -R keygap-sovereign-node:80:127.0.0.1:8100 serveo.net

kill $LOG_PID