#!/bin/bash
clear
echo -e "\033[1;31m===================================================\033[0m"
echo -e "\033[1;31m☠️  K-SOVEREIGN NODE: PROTOCOLLO BLINDATO ATTIVO ☠️\033[0m"
echo -e "\033[1;31m===================================================\033[0m"

# --- KILL SWITCH ASSOLUTO ---
cleanup() {
    echo -e "\n\033[1;33m[!] COMANDO MANUALE (CTRL+C) RILEVATO. Spegnimento totale in corso...\033[0m"
    # Disarma il trap per evitare loop di chiusura
    trap - SIGINT SIGTERM EXIT
    
    # 1. Uccide tutti i sottomotori in loop generati da questo script
    pkill -P $$ > /dev/null 2>&1
    
    # 2. Uccide i processi fisici e chiude la porta
    pkill -9 -f "keygap_bot.py" > /dev/null 2>&1
    pkill -9 -f "keygap_broadcaster.py" > /dev/null 2>&1
    pkill -9 -f "ssh.*serveo" > /dev/null 2>&1
    fuser -k 8100/tcp > /dev/null 2>&1
    
    echo -e "\033[1;32m[✓] Sistema disattivato con successo. Nodo Offline.\033[0m"
    exit 0
}

# La trappola ora scatta per SIGINT (Ctrl+C), SIGTERM, e anche in caso di EXIT naturale
trap cleanup SIGINT SIGTERM EXIT

# --- PULIZIA PRE-AVVIO ---
pkill -9 -f "keygap_bot.py" > /dev/null 2>&1
pkill -9 -f "keygap_broadcaster.py" > /dev/null 2>&1
pkill -9 -f "ssh.*serveo" > /dev/null 2>&1
fuser -k 8100/tcp > /dev/null 2>&1

while fuser 8100/tcp >/dev/null 2>&1; do
    fuser -k 8100/tcp > /dev/null 2>&1
    sleep 1
done

# --- MOTORE 1: BROADCASTER IMMORTALE ---
(
  while true; do
    python3 -u keygap_broadcaster.py >> broadcaster.log 2>&1
    sleep 2
  done
) &

# --- MOTORE 2: RADAR RICERCA IMMORTALE ---
> output.log
(
  while true; do
    python3 -u keygap_bot.py >> output.log 2>&1
    fuser -k 8100/tcp > /dev/null 2>&1
    sleep 2
  done
) &

# --- TUNNEL SERVEO BLINDATO ---
(
  while true; do
    ssh -o ServerAliveInterval=30 -o ServerAliveCountMax=3 -o StrictHostKeyChecking=no -R keygap-sovereign-node:80:127.0.0.1:8100 serveo.net > /dev/null 2>&1
    sleep 3
  done
) &

# Mostra i log a schermo ma lo fa in background
tail -f output.log &

# Questo comando è il vero segreto: blocca lo script principale in attesa.
# Quando premi Ctrl+C, interrompe l'attesa e fa scattare il Kill Switch perfetto.
wait