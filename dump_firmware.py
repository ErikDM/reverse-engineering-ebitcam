import re
import sys
import time
import serial
from pathlib import Path

PROMPT = b"GM #"
PROMPT_RE = re.compile(rb"\bGM\s*#\s*$", re.M)
MD_LINE_RE = re.compile(r"^\s*([0-9A-Fa-f]{8})\s*:\s*(.*)$")

def wait_for_prompt_with_ctrlc(ser: serial.Serial, timeout_s: float = 60.0, ctrlc_period_s: float = 0.3):
    buf = bytearray()
    start = time.time()
    last_ctrlc = 0.0
    print("[+] Waiting for U-Boot prompt (GM #)... (sending Ctrl+C)")

    while time.time() - start < timeout_s:
        data = ser.read(4096)
        if data:
            buf.extend(data)
            try:
                sys.stdout.write(data.decode("utf-8", errors="ignore"))
                sys.stdout.flush()
            except Exception:
                pass

        now = time.time()
        if now - last_ctrlc > ctrlc_period_s:
            ser.write(b"\x03")  # Ctrl+C
            ser.flush()
            last_ctrlc = now

        tail = bytes(buf[-1200:]).replace(b"\r", b"")
        lines = tail.split(b"\n")
        for line in reversed(lines):
            if not line.strip():
                continue
            if PROMPT_RE.search(line.strip()):
                print("\n[+] U-Boot prompt detected.")
                return
            break

        time.sleep(0.02)

    raise TimeoutError("Timed out waiting for GM # prompt.")

def read_until_prompt(ser: serial.Serial, timeout_s: float = 30.0) -> bytes:
    buf = bytearray()
    start = time.time()
    while time.time() - start < timeout_s:
        data = ser.read(4096)
        if data:
            buf.extend(data)
            # fast prompt check on tail
            tail = bytes(buf[-1200:]).replace(b"\r", b"")
            lines = tail.split(b"\n")
            for line in reversed(lines):
                if not line.strip():
                    continue
                if PROMPT_RE.search(line.strip()):
                    return bytes(buf)
                break
        else:
            time.sleep(0.02)
    raise TimeoutError("Timed out waiting for prompt after command.")

def send_cmd(ser: serial.Serial, cmd: str):
    ser.write((cmd + "\r\n").encode("ascii"))
    ser.flush()

def parse_md_output(text: str, expected_addr: int, expected_len: int) -> bytes:

    out = bytearray()
    next_addr = expected_addr

    for line in text.splitlines():
        m = MD_LINE_RE.match(line)
        if not m:
            continue

        addr = int(m.group(1), 16)
        if addr < expected_addr or addr >= expected_addr + expected_len:
            continue

        tokens = re.findall(r"\b[0-9A-Fa-f]{2}\b", m.group(2))
        chunk = bytes(int(t, 16) for t in tokens)

        if addr > next_addr:
            out.extend(b"\x00" * (addr - next_addr))
            next_addr = addr

        if addr < next_addr:
            # repeated / out-of-order line
            continue

        out.extend(chunk)
        next_addr += len(chunk)

        if len(out) >= expected_len:
            break

    if len(out) < expected_len:
        out.extend(b"\x00" * (expected_len - len(out)))

    return bytes(out[:expected_len])

def main():
    if len(sys.argv) < 3:
        print("Usage: python dump.py COM6 firmware.bin")
        sys.exit(1)

    port = sys.argv[1]
    out_path = Path(sys.argv[2])

    # These match your setup
    baud = 115200
    ram_base = 0x02000000
    flash_len = 0x01000000
    chunk_len = 0x2000

    ser = serial.Serial(
        port=port,
        baudrate=baud,
        bytesize=serial.EIGHTBITS,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        timeout=0.2,
        xonxoff=False,
        rtscts=False,
        dsrdtr=False,
    )

    try:
        try:
            ser.setDTR(False)
            ser.setRTS(False)
        except Exception:
            pass

        print(f"[+] Connected to {port} @ {baud}")

        wait_for_prompt_with_ctrlc(ser, timeout_s=60.0)

        print("[+] sf probe")
        send_cmd(ser, "sf probe")
        read_until_prompt(ser, timeout_s=10.0)

        print("[+] sf read 16MiB -> RAM (this may take a few seconds)")
        send_cmd(ser, f"sf read 0x{ram_base:08x} 0x00000000 0x{flash_len:08x}")
        read_until_prompt(ser, timeout_s=60.0)

        # dump loop
        print(f"[+] Dumping {flash_len} bytes via md.b in {chunk_len} byte chunks...")
        start = time.time()
        written = 0

        with out_path.open("wb") as f:
            for off in range(0, flash_len, chunk_len):
                addr = ram_base + off
                want = min(chunk_len, flash_len - off)

                cmd = f"md.b 0x{addr:08x} 0x{want:x}"
                send_cmd(ser, cmd)
                raw = read_until_prompt(ser, timeout_s=60.0)

                text = raw.decode("ascii", errors="ignore")
                block = parse_md_output(text, expected_addr=addr, expected_len=want)

                f.write(block)
                written += len(block)

                # progress
                elapsed = time.time() - start
                rate = written / elapsed if elapsed > 0 else 0
                pct = (written * 100.0) / flash_len
                print(f"    {pct:6.2f}%  {written}/{flash_len} bytes  ({rate/1024:.1f} KiB/s)")

        print(f"[+] Done: wrote {out_path} ({written} bytes)")
        print("[+] Next: run `binwalk firmware.bin` (or open in your analysis tools).")

    finally:
        ser.close()

if __name__ == "__main__":
    main()
