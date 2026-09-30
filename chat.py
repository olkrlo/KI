"""
  Terminal A :  python chat.py --mode listen  --name Alice
  Terminal B :  python chat.py --mode connect --name Bob --host <IP_A>
"""
import argparse, socket, sys, threading, time
from des import encrypt_cbc, decrypt_cbc

def recv_exact(sock, n):
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            return None
        buf += chunk
    return buf

def send_msg(sock, text, key, name):
    payload = encrypt_cbc(text.encode("utf-8"), key)          # IV + ciphertext
    print(f"  [{name}] plaintext  : {text}")
    print(f"  [{name}] ciphertext : {payload[8:].hex()}  (IV={payload[:8].hex()})")
    sock.sendall(len(payload).to_bytes(4, "big") + payload)

def receiver_loop(sock, key, name, stop):
    while not stop.is_set():
        hdr = recv_exact(sock, 4)
        if hdr is None:
            print("\n[!] Lawan bicara terputus."); stop.set(); break
        payload = recv_exact(sock, int.from_bytes(hdr, "big"))
        print(f"\n  [{name}] DITERIMA ciphertext : {payload[8:].hex()}")
        try:
            print(f"  [{name}] hasil dekripsi      : {decrypt_cbc(payload, key).decode('utf-8')}")
        except Exception as e:
            print(f"  [{name}] gagal dekripsi ({e})")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["listen", "connect"], required=True)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=5000)
    ap.add_argument("--name", default="Peer")
    ap.add_argument("--key", default="kunciKI8", help="tepat 8 karakter, sama di kedua sisi")
    ap.add_argument("--auto", help="file berisi pesan otomatis (1 baris = 1 pesan), untuk demo")
    ap.add_argument("--delay", type=float, default=2.0, help="jeda antar pesan mode --auto")
    a = ap.parse_args()
    key = a.key.encode()
    if len(key) != 8:
        sys.exit("Key harus tepat 8 karakter")

    if a.mode == "listen":
        srv = socket.socket(); srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(("0.0.0.0", a.port)); srv.listen(1)
        print(f"[{a.name}] menunggu koneksi di port {a.port} ...")
        sock, addr = srv.accept()
        print(f"[{a.name}] terhubung dengan {addr}")
    else:
        sock = socket.socket()
        for _ in range(20):                       # retry sampai server siap
            try: sock.connect((a.host, a.port)); break
            except ConnectionRefusedError: time.sleep(0.5)
        else:
            sys.exit("Gagal terhubung ke server")
        print(f"[{a.name}] terhubung ke {a.host}:{a.port}")

    stop = threading.Event()
    threading.Thread(target=receiver_loop, args=(sock, key, a.name, stop), daemon=True).start()

    try:
        if a.auto:                                # mode demo otomatis
            with open(a.auto, encoding="utf-8") as f:
                for line in f:
                    if stop.is_set(): break
                    line = line.strip()
                    if line:
                        time.sleep(a.delay); send_msg(sock, line, key, a.name)
            time.sleep(a.delay * 2)
        else:                                     # mode interaktif
            print("Ketik pesan lalu Enter (ketik 'exit' untuk keluar)")
            while not stop.is_set():
                line = sys.stdin.readline()
                if not line or line.strip().lower() == "exit": break
                if line.strip(): send_msg(sock, line.strip(), key, a.name)
    finally:
        stop.set(); sock.close()

if __name__ == "__main__":
    main()
