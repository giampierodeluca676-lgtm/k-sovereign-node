#!/bin/bash
clear
echo -e "\033[1;35m"
echo "==============================================================================================="
echo "                         K-SOVEREIGN INTELLIGENCE DASHBOARD v15.0                              "
echo "==============================================================================================="
echo -e "\033[1;37m ORARIO   | AZIONE       | IP CLIENT       | LOCALITÀ                          | DEVICE     | DETTAGLIO"
echo "-----------------------------------------------------------------------------------------------"
echo -e "\033[0m"

# 1. Reset Chirurgico
pkill -f "keygap_bot.py" > /dev/null 2>&1
pkill -f "127.0.0.1:8100" > /dev/null 2>&1
fuser -k 8100/tcp > /dev/null 2>&1
sleep 1

# 2. Avvio Motore e Tailing pulito
> output.log
python3 -u keygap_bot.py >> output.log 2>&1 &
tail -f output.log &
LOG_PID=$!

# 3. Apertura Tunnel FISSO
ssh -o ServerAliveInterval=60 -R keygap-sovereign-node:80:127.0.0.1:8100 serveo.net

kill $LOG_PID