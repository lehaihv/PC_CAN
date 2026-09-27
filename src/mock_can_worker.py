"""
Mock CAN worker for development and UI testing without real hardware.

Drop-in replacement for CanWorker — identical public signal/slot interface.

Simulated CAN protocol (mirrors qml_bridge.py constants):
  0x101  Motor RPM   – bytes[0:2] big-endian uint16
  0x102  Temperature – bytes[0:4] big-endian float32 °C
  0x103  Voltage     – bytes[0:4] big-endian float32 V

NEVER uses time.sleep() or blocking loops.  All periodic work runs via QTimer.
"""

import csv
import random
import struct
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QObject, QTimer, Signal, Slot

# CSV log path — written next to the src/ directory
_LOG_PATH: Path = Path(__file__).parent.parent / "mock_can_log.csv"

# CAN IDs
_ID_RPM:   int = 0x101
_ID_TEMP:  int = 0x102
_ID_VOLT:  int = 0x103


class MockCanWorker(QObject):
    """
    Timer-driven mock of the CAN hardware worker.

    All periodic operations use QTimer so the GUI thread event loop is
    never blocked.

    Signals (identical to CanWorker)
    ---------------------------------
    message_received(int, list[int])
    error_occurred(str)

    Extra signals
    -------------
    file_loaded(str)        – emitted after a successful simulated load
    file_load_error(str)    – emitted on a simulated 10% load failure
    connection_changed(bool)– emitted when mock connect state changes
    """

    # ── Core interface (must match CanWorker exactly) ──────────────────
    message_received: Signal = Signal(int, list)
    error_occurred:   Signal = Signal(str)

    # ── Extra mock signals ─────────────────────────────────────────────
    file_loaded:        Signal = Signal(str)
    file_load_error:    Signal = Signal(str)
    connection_changed: Signal = Signal(bool)

    # ── Timing constants ───────────────────────────────────────────────
    _TICK_MS:     int = 500     # main data frame interval
    _ERROR_MS:    int = 20_000  # periodic simulated bus error

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)

        # ── Simulation state ──────────────────────────────────────────
        self._rpm:     float = 0.0
        self._rpm_target: float = 0.0
        self._temp:    float = 25.0
        self._temp_dir: int  = 1       # +1 heating, -1 cooling
        self._volt:    float = 12.6

        # ── Timers ────────────────────────────────────────────────────
        self._data_timer:  QTimer = QTimer(self)
        self._error_timer: QTimer = QTimer(self)

        self._data_timer.setInterval(self._TICK_MS)
        self._data_timer.timeout.connect(self._on_tick)

        self._error_timer.setInterval(self._ERROR_MS)
        self._error_timer.timeout.connect(self._on_simulated_error)

        # ── CSV log ───────────────────────────────────────────────────
        self._csv_file = open(_LOG_PATH, "w", newline="", encoding="utf-8")
        self._csv_writer = csv.writer(self._csv_file)
        self._csv_writer.writerow(["timestamp_ms", "can_id", "data_hex"])
        self._elapsed_ms: int = 0

    # ------------------------------------------------------------------
    # Public slots — identical API to CanWorker
    # ------------------------------------------------------------------

    @Slot()
    def start_listening(self) -> None:
        """Start all timers and begin emitting simulated CAN frames."""
        self._elapsed_ms = 0
        self._rpm        = 0.0
        self._rpm_target = random.uniform(500, 3000)
        self._temp       = 25.0
        self._temp_dir   = 1
        self._volt       = 12.6

        self._data_timer.start()
        self._error_timer.start()
        print("[MockCAN] start_listening: timers started.")

    @Slot()
    def stop(self) -> None:
        """Stop all timers and close the CSV log."""
        self._data_timer.stop()
        self._error_timer.stop()

        # Flush and close CSV
        self._csv_file.flush()
        self._csv_file.close()

        self.error_occurred.emit("Mock worker stopped.")
        print("[MockCAN] stop: all timers stopped, CSV log closed.")

    @Slot(int, list)
    def send_message(self, can_id: int, data: list[int]) -> None:
        """
        Log a transmitted frame to the console and emit it back as a
        received frame (simulating CAN bus loopback) so it appears in
        the UI log and updates the bridge properties.
        """
        # QML passes JS numbers as floats — coerce to int before formatting
        safe_data: list[int] = [int(b) for b in data]
        hex_data: str = " ".join(f"{b:02X}" for b in safe_data)
        print(f"[MockCAN] TX  ID=0x{can_id:03X}  [{len(safe_data)}]  {hex_data}")

        self.message_received.emit(can_id, safe_data)

    # ------------------------------------------------------------------
    # Extra mock slots — connection simulation
    # ------------------------------------------------------------------

    @Slot()
    def simulate_disconnect(self) -> None:
        """Simulate a sudden bus disconnect."""
        self._data_timer.stop()
        self.connection_changed.emit(False)
        self.error_occurred.emit("Simulated disconnect.")
        print("[MockCAN] simulate_disconnect called.")

    @Slot()
    def simulate_reconnect(self) -> None:
        """Simulate a bus reconnect after a disconnect."""
        if not self._data_timer.isActive():
            self._data_timer.start()
        self.connection_changed.emit(True)
        print("[MockCAN] simulate_reconnect called.")

    # ------------------------------------------------------------------
    # Extra mock slot — file loading simulation
    # ------------------------------------------------------------------

    @Slot(str)
    def load_file(self, path: str) -> None:
        """
        Simulate loading a config file.

        Resolves after a 2 s delay.  10 % of the time emits
        ``file_load_error`` instead of ``file_loaded``.
        """
        print(f"[MockCAN] load_file: simulating 2 s load for '{path}'")

        def _finish() -> None:
            if random.random() < 0.10:
                self.file_load_error.emit(
                    f"Simulated read error for '{path}'"
                )
                print(f"[MockCAN] load_file: FAILED (simulated 10% error)")
            else:
                self.file_loaded.emit(path)
                print(f"[MockCAN] load_file: SUCCESS '{path}'")

        QTimer.singleShot(2_000, _finish)

    # ------------------------------------------------------------------
    # Private — timer callbacks
    # ------------------------------------------------------------------

    @Slot()
    def _on_tick(self) -> None:
        """Called every _TICK_MS ms. Advances simulation and emits frames."""
        self._elapsed_ms += self._TICK_MS

        self._update_rpm()
        self._update_temp()
        self._update_volt()

        # Emit one frame per metric per tick
        self._emit(
            _ID_RPM,
            list(struct.pack(">H", max(0, min(65535, int(self._rpm))))),
        )
        self._emit(
            _ID_TEMP,
            list(struct.pack(">f", self._temp)),
        )
        self._emit(
            _ID_VOLT,
            list(struct.pack(">f", self._volt)),
        )

    @Slot()
    def _on_simulated_error(self) -> None:
        """Emit a periodic simulated bus timeout (every 20 s)."""
        self.error_occurred.emit("Simulated bus timeout on PCAN_USBBUS1.")
        print("[MockCAN] Simulated bus timeout emitted.")

    # ------------------------------------------------------------------
    # Private — simulation model
    # ------------------------------------------------------------------

    def _update_rpm(self) -> None:
        """
        Smooth RPM toward a random target.
        Pick a new target every time we get within 50 RPM of the current one.
        """
        delta = self._rpm_target - self._rpm
        if abs(delta) < 50:
            self._rpm_target = random.uniform(0, 5000)
        # Accelerate / decelerate at up to 200 RPM per tick
        step = min(abs(delta), 200) * (1 if delta > 0 else -1)
        self._rpm = max(0.0, min(5000.0, self._rpm + step))

    def _update_temp(self) -> None:
        """
        Temperature drifts from 25 °C up to 80 °C then cools back down.
        Small random noise (±0.5 °C) added each tick.
        """
        self._temp += self._temp_dir * random.uniform(0.1, 0.5)
        noise = random.uniform(-0.5, 0.5)
        self._temp = round(self._temp + noise, 2)
        if self._temp >= 80.0:
            self._temp_dir = -1
        elif self._temp <= 25.0:
            self._temp_dir = 1

    def _update_volt(self) -> None:
        """Voltage hovers around 12.6 V with ±0.2 V noise."""
        self._volt = round(12.6 + random.uniform(-0.2, 0.2), 3)

    # ------------------------------------------------------------------
    # Private — helpers
    # ------------------------------------------------------------------

    def _emit(self, can_id: int, data: list[int]) -> None:
        """Emit a frame and log it to the CSV file."""
        self.message_received.emit(can_id, data)

        hex_data = " ".join(f"{b:02X}" for b in data)
        self._csv_writer.writerow([self._elapsed_ms, f"0x{can_id:03X}", hex_data])
        self._csv_file.flush()
