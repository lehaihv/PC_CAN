"""
Mock CAN worker — drop-in replacement for CanWorker.

Emits all 13 simulated metrics every 500 ms via QTimer (no blocking).

CAN ID protocol (mirrors qml_bridge.py):
  0x101 Motor RPM      uint16
  0x102 Temperature    float32 °C
  0x103 Voltage        float32 V
  0x104 Current        float32 A
  0x105 Vehicle Speed  uint16  km/h
  0x106 Fuel Rate      float32 L/h
  0x107 Throttle       float32 %
  0x108 TBL            float32 kg
  0x109 SWY            float32 kg
  0x10A DRG            float32 kg
  0x10B ACC_X          float32 g
  0x10C ACC_Y          float32 g
  0x10D ACC_Z          float32 g
"""

import math
import random
import struct
from typing import Optional

from PySide6.QtCore import QObject, QTimer, Signal, Slot

_ID_RPM      = 0x101
_ID_TEMP     = 0x102
_ID_VOLT     = 0x103
_ID_CURRENT  = 0x104
_ID_SPEED    = 0x105
_ID_FUEL     = 0x106
_ID_THROTTLE = 0x107
_ID_TBL      = 0x108
_ID_SWY      = 0x109
_ID_DRG      = 0x10A
_ID_ACC_X    = 0x10B
_ID_ACC_Y    = 0x10C
_ID_ACC_Z    = 0x10D


def _f32(v: float) -> list[int]:
    return list(struct.pack(">f", v))

def _u16(v: int) -> list[int]:
    return list(struct.pack(">H", max(0, min(65535, v))))


class MockCanWorker(QObject):
    """Timer-driven mock — all signals identical to CanWorker."""

    message_received: Signal = Signal(int, list)
    error_occurred:   Signal = Signal(str)
    file_loaded:        Signal = Signal(str)
    file_load_error:    Signal = Signal(str)
    connection_changed: Signal = Signal(bool)

    _TICK_MS  = 500
    _ERROR_MS = 20_000

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._t:            float = 0.0   # elapsed seconds

        # ── Simulation state ──────────────────────────────────────────
        # RPM — smooth random walk
        self._rpm:        float = 0.0
        self._rpm_target: float = 1500.0

        # Temperature — sawtooth 25→80→25 °C
        self._temp:     float = 25.0
        self._temp_dir: int   = 1

        # Voltage
        self._volt: float = 12.6

        # Current — tracks RPM loosely
        self._current: float = 0.0

        # Vehicle speed — smooth random walk 0–250 km/h
        self._speed:        float = 0.0
        self._speed_target: float = 80.0

        # Fuel rate — linked to throttle
        self._fuel: float = 5.0

        # Throttle — random walk 0–100 %
        self._throttle:        float = 20.0
        self._throttle_target: float = 30.0

        # Load cells — slow drift around a centre
        self._tbl: float = 120.0
        self._swy: float = 0.0
        self._drg: float = 50.0

        # Accelerometer — mostly 0 g except Z ≈ 1 g (gravity)
        self._acc_x: float = 0.0
        self._acc_y: float = 0.0
        self._acc_z: float = 1.0

        # ── Timers ────────────────────────────────────────────────────
        self._data_timer  = QTimer(self)
        self._error_timer = QTimer(self)
        self._data_timer.setInterval(self._TICK_MS)
        self._data_timer.timeout.connect(self._on_tick)
        self._error_timer.setInterval(self._ERROR_MS)
        self._error_timer.timeout.connect(self._on_error)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @Slot()
    def start_listening(self) -> None:
        self._t = 0.0
        self._data_timer.start()
        self._error_timer.start()
        print("[MockCAN] start_listening: timers started.")

    @Slot()
    def stop(self) -> None:
        self._data_timer.stop()
        self._error_timer.stop()
        self.error_occurred.emit("Mock worker stopped.")
        print("[MockCAN] stop: all timers stopped.")

    @Slot(int, list)
    def send_message(self, can_id: int, data: list[int]) -> None:
        safe = [int(b) for b in data]
        print(f"[MockCAN] TX  ID=0x{can_id:03X}  [{len(safe)}]  {' '.join(f'{b:02X}' for b in safe)}")
        self.message_received.emit(can_id, safe)

    @Slot()
    def simulate_disconnect(self) -> None:
        self._data_timer.stop()
        self.connection_changed.emit(False)
        self.error_occurred.emit("Simulated disconnect.")

    @Slot()
    def simulate_reconnect(self) -> None:
        if not self._data_timer.isActive():
            self._data_timer.start()
        self.connection_changed.emit(True)

    @Slot(str)
    def load_file(self, path: str) -> None:
        def _finish() -> None:
            if random.random() < 0.10:
                self.file_load_error.emit(f"Simulated read error for '{path}'")
            else:
                self.file_loaded.emit(path)
        QTimer.singleShot(2_000, _finish)

    # ------------------------------------------------------------------
    # Private — tick
    # ------------------------------------------------------------------

    @Slot()
    def _on_tick(self) -> None:
        self._t += self._TICK_MS / 1000.0
        t = self._t

        # RPM — smooth toward random target
        self._rpm = self._smooth(self._rpm, self._rpm_target, 300)
        if abs(self._rpm - self._rpm_target) < 100:
            self._rpm_target = random.uniform(0, 5000)
        rpm_val = int(self._rpm)

        # Temperature — sawtooth with noise
        self._temp += self._temp_dir * random.uniform(0.05, 0.3)
        self._temp += random.uniform(-0.2, 0.2)
        self._temp = round(self._temp, 2)
        if self._temp >= 80.0: self._temp_dir = -1
        elif self._temp <= 25.0: self._temp_dir = 1

        # Voltage — small noise
        volt = round(12.6 + random.uniform(-0.2, 0.2), 3)

        # Current — proportional to RPM with noise
        current = round(self._rpm / 5000.0 * 40.0 + random.uniform(-0.5, 0.5), 2)
        current = max(0.0, current)

        # Vehicle speed — smooth toward target
        self._speed = self._smooth(self._speed, self._speed_target, 5)
        if abs(self._speed - self._speed_target) < 5:
            self._speed_target = random.uniform(0, 250)
        speed_val = int(round(self._speed))

        # Throttle — smooth random walk 0–100 %
        self._throttle = self._smooth(self._throttle, self._throttle_target, 3)
        if abs(self._throttle - self._throttle_target) < 2:
            self._throttle_target = random.uniform(0, 100)
        throttle = round(max(0.0, min(100.0, self._throttle)), 2)

        # Fuel rate — linked to throttle + noise
        fuel = round(throttle / 100.0 * 25.0 + random.uniform(-0.1, 0.1), 2)
        fuel = max(0.0, fuel)

        # Load cells — slow sine drift + noise
        tbl = round(1200.0 + 80.0 * math.sin(t * 0.05) + random.uniform(-1, 1), 2)
        swy = round(      5.0 * math.sin(t * 0.1)  + random.uniform(-0.5, 0.5), 2)
        drg = round( 500.0 + 50.0 * math.sin(t * 0.07) + random.uniform(-2, 2), 2)

        # Accelerometer — vibration model
        acc_x = round(0.1 * math.sin(t * 2.3) + random.uniform(-0.05, 0.05), 3)
        acc_y = round(0.1 * math.cos(t * 1.7) + random.uniform(-0.05, 0.05), 3)
        acc_z = round(1.0 + 0.05 * math.sin(t * 3.1) + random.uniform(-0.02, 0.02), 3)

        # Emit all frames
        self._emit(_ID_RPM,      _u16(rpm_val))
        self._emit(_ID_TEMP,     _f32(self._temp))
        self._emit(_ID_VOLT,     _f32(volt))
        self._emit(_ID_CURRENT,  _f32(current))
        self._emit(_ID_SPEED,    _u16(speed_val))
        self._emit(_ID_FUEL,     _f32(fuel))
        self._emit(_ID_THROTTLE, _f32(throttle))
        self._emit(_ID_TBL,      _f32(tbl))
        self._emit(_ID_SWY,      _f32(swy))
        self._emit(_ID_DRG,      _f32(drg))
        self._emit(_ID_ACC_X,    _f32(acc_x))
        self._emit(_ID_ACC_Y,    _f32(acc_y))
        self._emit(_ID_ACC_Z,    _f32(acc_z))

    @Slot()
    def _on_error(self) -> None:
        self.error_occurred.emit("Simulated bus timeout on PCAN_USBBUS1.")

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _smooth(current: float, target: float, max_step: float) -> float:
        delta = target - current
        step  = min(abs(delta), max_step) * (1 if delta > 0 else -1)
        return current + step

    def _emit(self, can_id: int, data: list[int]) -> None:
        self.message_received.emit(can_id, data)
