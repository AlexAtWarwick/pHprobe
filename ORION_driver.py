import serial
import time
import logging
from datetime import datetime

# ---------- Logging ----------
class RedFormatter(logging.Formatter):
    RED = "\033[31m"
    RESET = "\033[0m"
    def format(self, record):
        return f"{self.RED}{super().format(record)}{self.RESET}"

for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)
handler = logging.StreamHandler()
formatter = RedFormatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger = logging.getLogger()
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# ---------- Error ----------
class OrionError(Exception):
    """Custom exception for OrionControl operations."""
    pass

# ---------- OrionControl Class ----------
class OrionControl:
    """Class to control Orion pH/Conductivity meter via serial."""
    def __init__(self, port='COM11', timeout=1):
        try:
            self.ser = serial.Serial(
                port=port,
                baudrate=9600,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=timeout
            )
            logger.info(f"[OrionControl] Connected to {port}")
        except serial.SerialException as e:
            raise OrionError(f"[OrionControl] Serial connection error: {e}")

    def _clean_channel(self, data):
        if data[0] in ('pH', 'COND'):
            return {
                "probe mode": data[0],
                "Value": data[1],
                "Units": data[2],
                "Temperature": data[5],
                "Temperature units": data[6]
            }
        raise OrionError(f"[OrionControl] Invalid probe mode in: {data}")

    def _parse_response(self, lines):
        try:
            raw = lines[2]
            data = raw.split(',')
            ch1 = ch2 = None

            if 'CH-1' in data:
                idx1 = data.index('CH-1')
                idx2 = data.index('CH-2') if 'CH-2' in data else len(data)
                ch1 = self._clean_channel(data[idx1+1:idx2])

            if 'CH-2' in data:
                idx2 = data.index('CH-2')
                ch2 = self._clean_channel(data[idx2+1:])

            return ch1, ch2

        except Exception as e:
            raise OrionError(f"[OrionControl] Failed to parse response: {e}")

    def get_measurement(self):
        """Request a single measurement and return structured result."""
        try:
            self.ser.reset_input_buffer()
            self.ser.write(b'GETMEAS\r')
            time.sleep(0.5)

            lines = []
            while self.ser.in_waiting:
                line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                lines.append(line)
                time.sleep(0.05)

            ch1, ch2 = self._parse_response(lines)

            # Default values
            ph = ph_temp = cond = cond_temp = "N/A"

            for ch in (ch1, ch2):
                if not ch:
                    continue
                if ch["probe mode"] == "pH":
                    ph = ch["Value"]
                    ph_temp = ch["Temperature"]
                elif ch["probe mode"] == "COND":
                    cond = ch["Value"]
                    cond_temp = ch["Temperature"]

            logger.info(f"[OrionControl] pH: {ph} @ {ph_temp}C | Conductivity: {cond} @ {cond_temp}C")

            return {
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "ph": ph,
                "ph_temp": ph_temp,
                "conductivity": cond,
                "cond_temp": cond_temp
            }

        except OrionError as e:
            logger.error(e)
            return None
        except Exception as e:
            logger.error(f"[OrionControl] Unexpected error: {e}")
            return None

    def close(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
            logger.info("[OrionControl] Serial connection closed.")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

