#!/bin/bash
while true; do
    echo "--- [K-SOVEREIGN NODE] IN AVVIO ---"
    python3 -u keygap_bot.py
    echo "--- [!] CRASH O RIAVVIO RILEVATO. RE-BOOT IN 5 SECONDI ---"
    sleep 5
done
