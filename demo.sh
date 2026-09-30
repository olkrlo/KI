#!/bin/bash
# Demo otomatis: Alice (listen) & Bob (connect) saling kirim pesan
python3 chat.py --mode listen  --name Alice --auto pesan_alice.txt --delay 2 &
sleep 1
python3 chat.py --mode connect --name Bob   --auto pesan_bob.txt   --delay 3
wait
