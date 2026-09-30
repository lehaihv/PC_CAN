"""
QML Bridge — thread-safe adapter between QML and the CAN worker.

CSV logging is user-controlled: call startLogging(path) / stopLogging().
No file is ever opened automatically.
"""

import csv
import struct
from datetime import datetime
from pathlib import Path
from typing import Union, Optional

from PySide6.QtCore import Property, QObject, Signal, Slot

from can_worker import CanWorker
from mock_can_worker import MockCanWorker

AnyWorker = Union[CanWorker, MockCanWorker]

# ---------------------------------------------------------------------------
# CAN ID → property mapping  (ESP32-S3 firmware protocol)
# ---------------------------------------------------------------------------
_ID_RPM:      int = 0x101   # uint16  big-endian
_ID_TEMP:     int = 0x102   # float32 big-endian  °C
_ID_VOLT:     int = 0x103   # float32 big-endian  V
_ID_CURRENT:  int = 0x104   # float32 big-endian  A
_ID_SPEED:    int = 0x105   # uint16  big-endian  km/h
_ID_FUEL:     int = 0x106   # float32 big-endian  L/h
_ID_THROTTLE: int = 0x107   # float32 big-endian  %
_ID_TBL:      int = 0x108   # float32 big-endian  kg
_ID_SWY:      int = 0x109   # float32 big-endian  kg
_ID_DRG:      int = 0x10A   # float32 big-endian  kg
_ID_ACC_X:    int = 0x10B   # float32 big-endian  g
_ID_ACC_Y:    int = 0x10C   # float32 big-endian  g
_ID_ACC_Z:    int = 0x10D   # float32 big-endian  g


def _f32(data: list[int]) -> float:
    return struct.unpack(">f", bytes(data[:4]))[0]

def _u16(data: list[int]) -> int:
    return struct.unpack(">H", bytes(data[:2]))[0]


class QmlBridge(QObject):
    """
    Thread-safe bridge — lives on the GUI thread.

    QML properties: isConnected, isRunning, isLogging, logFilePath,
    selectedConfig, motorRpm, temperature, voltage, current,
    vehicleSpeed, fuelRate, throttle, tbl, swy, drg, accX, accY, accZ,
    statusLog.
    """

    # ── Change-notification signals ────────────────────────────────────
    isConnectedChanged:    Signal = Signal()
    isRunningChanged:      Signal = Signal()
    isLoggingChanged:      Signal = Signal()
    logFilePathChanged:    Signal = Signal()
    selectedConfigChanged: Signal = Signal()
    motorRpmChanged:       Signal = Signal()
    temperatureChanged:    Signal = Signal()
    voltageChanged:        Signal = Signal()
    currentChanged:        Signal = Signal()
    vehicleSpeedChanged:   Signal = Signal()
    fuelRateChanged:       Signal = Signal()
    throttleChanged:       Signal = Signal()
    tblChanged:            Signal = Signal()
    swyChanged:            Signal = Signal()
    drgChanged:            Signal = Signal()
    accXChanged:           Signal = Signal()
    accYChanged:           Signal = Signal()
    accZChanged:           Signal = Signal()
    statusLogChanged:      Signal = Signal()
    logMessage:            Signal = Signal(str)

    def __init__(self, worker: AnyWorker, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._worker:  AnyWorker = worker
        self._is_mock: bool      = isinstance(worker, MockCanWorker)

        # Backing fields
        self._is_connected:    bool  = False
        self._is_running:      bool  = False
        self._is_logging:      bool  = False
        self._log_file_path:   str   = ""
        self._selected_config: str   = ""
        self._motor_rpm:       int   = 0
        self._temperature:     float = 0.0
        self._voltage:         float = 0.0
        self._current:         float = 0.0
        self._vehicle_speed:   int   = 0
        self._fuel_rate:       float = 0.0
        self._throttle:        float = 0.0
        self._tbl:             float = 0.0
        self._swy:             float = 0.0
        self._drg:             float = 0.0
        self._acc_x:           float = 0.0
        self._acc_y:           float = 0.0
        self._acc_z:           float = 0.0
        self._status_log:      str   = ""

        self._csv_file:   Optional[object] = None
        self._csv_writer: Optional[object] = None

        self._worker.message_received.connect(self._on_message_received)
        self._worker.error_occurred.connect(self._on_error_occurred)
        if self._is_mock:
            m = self._worker  # type: ignore[assignment]
            m.file_loaded.connect(self._on_file_loaded)
            m.file_load_error.connect(self._on_file_load_error)
            m.connection_changed.connect(self._on_connection_changed)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @Property(bool, notify=isConnectedChanged)
    def isConnected(self) -> bool: return self._is_connected
    @isConnected.setter
    def isConnected(self, v: bool) -> None:
        if self._is_connected != v: self._is_connected = v; self.isConnectedChanged.emit()

    @Property(bool, notify=isRunningChanged)
    def isRunning(self) -> bool: return self._is_running
    @isRunning.setter
    def isRunning(self, v: bool) -> None:
        if self._is_running != v: self._is_running = v; self.isRunningChanged.emit()

    @Property(bool, notify=isLoggingChanged)
    def isLogging(self) -> bool: return self._is_logging
    @isLogging.setter
    def isLogging(self, v: bool) -> None:
        if self._is_logging != v: self._is_logging = v; self.isLoggingChanged.emit()

    @Property(str, notify=logFilePathChanged)
    def logFilePath(self) -> str: return self._log_file_path
    @logFilePath.setter
    def logFilePath(self, v: str) -> None:
        if self._log_file_path != v: self._log_file_path = v; self.logFilePathChanged.emit()

    @Property(str, notify=selectedConfigChanged)
    def selectedConfig(self) -> str: return self._selected_config
    @selectedConfig.setter
    def selectedConfig(self, v: str) -> None:
        if self._selected_config != v: self._selected_config = v; self.selectedConfigChanged.emit()

    @Property(int, notify=motorRpmChanged)
    def motorRpm(self) -> int: return self._motor_rpm
    @motorRpm.setter
    def motorRpm(self, v: int) -> None:
        if self._motor_rpm != v: self._motor_rpm = v; self.motorRpmChanged.emit()

    @Property(float, notify=temperatureChanged)
    def temperature(self) -> float: return self._temperature
    @temperature.setter
    def temperature(self, v: float) -> None:
        if self._temperature != v: self._temperature = v; self.temperatureChanged.emit()

    @Property(float, notify=voltageChanged)
    def voltage(self) -> float: return self._voltage
    @voltage.setter
    def voltage(self, v: float) -> None:
        if self._voltage != v: self._voltage = v; self.voltageChanged.emit()

    @Property(float, notify=currentChanged)
    def current(self) -> float: return self._current
    @current.setter
    def current(self, v: float) -> None:
        if self._current != v: self._current = v; self.currentChanged.emit()

    @Property(int, notify=vehicleSpeedChanged)
    def vehicleSpeed(self) -> int: return self._vehicle_speed
    @vehicleSpeed.setter
    def vehicleSpeed(self, v: int) -> None:
        if self._vehicle_speed != v: self._vehicle_speed = v; self.vehicleSpeedChanged.emit()

    @Property(float, notify=fuelRateChanged)
    def fuelRate(self) -> float: return self._fuel_rate
    @fuelRate.setter
    def fuelRate(self, v: float) -> None:
        if self._fuel_rate != v: self._fuel_rate = v; self.fuelRateChanged.emit()

    @Property(float, notify=throttleChanged)
    def throttle(self) -> float: return self._throttle
    @throttle.setter
    def throttle(self, v: float) -> None:
        if self._throttle != v: self._throttle = v; self.throttleChanged.emit()

    @Property(float, notify=tblChanged)
    def tbl(self) -> float: return self._tbl
    @tbl.setter
    def tbl(self, v: float) -> None:
        if self._tbl != v: self._tbl = v; self.tblChanged.emit()

    @Property(float, notify=swyChanged)
    def swy(self) -> float: return self._swy
    @swy.setter
    def swy(self, v: float) -> None:
        if self._swy != v: self._swy = v; self.swyChanged.emit()

    @Property(float, notify=drgChanged)
    def drg(self) -> float: return self._drg
    @drg.setter
    def drg(self, v: float) -> None:
        if self._drg != v: self._drg = v; self.drgChanged.emit()

    @Property(float, notify=accXChanged)
    def accX(self) -> float: return self._acc_x
    @accX.setter
    def accX(self, v: float) -> None:
        if self._acc_x != v: self._acc_x = v; self.accXChanged.emit()

    @Property(float, notify=accYChanged)
    def accY(self) -> float: return self._acc_y
    @accY.setter
    def accY(self, v: float) -> None:
        if self._acc_y != v: self._acc_y = v; self.accYChanged.emit()

    @Property(float, notify=accZChanged)
    def accZ(self) -> float: return self._acc_z
    @accZ.setter
    def accZ(self, v: float) -> None:
        if self._acc_z != v: self._acc_z = v; self.accZChanged.emit()

    @Property(str, notify=statusLogChanged)
    def statusLog(self) -> str: return self._status_log
    @statusLog.setter
    def statusLog(self, v: str) -> None:
        if self._status_log != v: self._status_log = v; self.statusLogChanged.emit()

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    @Slot()
    def startAcquisition(self) -> None:
        self.isConnected = True; self.isRunning = True
        self._append_log("Acquisition started.")

    @Slot()
    def stopAcquisition(self) -> None:
        self.isRunning = False
        self._append_log("Acquisition stopped.")

    @Slot()
    def requestLoadFile(self) -> None:
        self._append_log("Load file requested.")

    @Slot(str)
    def loadFile(self, file_url: str) -> None:
        self._append_log(f"Config loading: {file_url}")
        self.selectedConfig = file_url
        if self._is_mock:
            self._worker.load_file(file_url)  # type: ignore[union-attr]

    @Slot(int, list)
    def send_command(self, can_id: int, data: list[int]) -> None:
        safe: list[int] = [int(b) for b in data]
        self._csv_write("TX", can_id, safe)
        self._worker.send_message(can_id, safe)

    @Slot(str)
    def startLogging(self, file_url: str) -> None:
        if self._is_logging:
            self.stopLogging()
        path_str = file_url
        for prefix in ("file:///", "file://"):
            if path_str.startswith(prefix):
                path_str = path_str[len(prefix) - (1 if prefix.endswith("///") else 0):]
                break
        # Ensure leading slash on Linux
        if file_url.startswith("file:///") and not path_str.startswith("/"):
            path_str = "/" + path_str
        path = Path(path_str)
        try:
            self._csv_file   = open(path, "w", newline="", encoding="utf-8")
            self._csv_writer = csv.writer(self._csv_file)
            self._csv_writer.writerow(["wall_time", "direction", "can_id", "len", "data_hex"])  # type: ignore[union-attr]
            self._csv_file.flush()  # type: ignore[union-attr]
            self.logFilePath = str(path)
            self.isLogging   = True
            self._append_log(f"Logging started → {path.name}")
            print(f"[Bridge] CSV logging → {path}")
        except OSError as exc:
            self._append_log(f"ERR Cannot open log file: {exc}")
            self._csv_file = self._csv_writer = None

    @Slot()
    def stopLogging(self) -> None:
        if not self._is_logging or self._csv_file is None:
            return
        try:
            self._csv_file.flush()  # type: ignore[union-attr]
            self._csv_file.close()  # type: ignore[union-attr]
            self._append_log(f"Logging stopped — {Path(self._log_file_path).name}")
        except Exception:
            pass
        finally:
            self._csv_file = self._csv_writer = None
            self.isLogging = False

    @Slot()
    def simulateDisconnect(self) -> None:
        if self._is_mock: self._worker.simulate_disconnect()  # type: ignore[union-attr]
        else: self._append_log("simulateDisconnect: ignored (real hardware).")

    @Slot()
    def simulateReconnect(self) -> None:
        if self._is_mock: self._worker.simulate_reconnect()  # type: ignore[union-attr]
        else: self._append_log("simulateReconnect: ignored (real hardware).")

    # ------------------------------------------------------------------
    # Private — signal handlers
    # ------------------------------------------------------------------

    @Slot(int, list)
    def _on_message_received(self, can_id: int, data: list[int]) -> None:
        safe: list[int] = [int(b) for b in data]

        if   can_id == _ID_RPM      and len(safe) >= 2: self.motorRpm     = _u16(safe)
        elif can_id == _ID_TEMP     and len(safe) >= 4: self.temperature  = round(_f32(safe), 2)
        elif can_id == _ID_VOLT     and len(safe) >= 4: self.voltage      = round(_f32(safe), 3)
        elif can_id == _ID_CURRENT  and len(safe) >= 4: self.current      = round(_f32(safe), 2)
        elif can_id == _ID_SPEED    and len(safe) >= 2: self.vehicleSpeed = _u16(safe)
        elif can_id == _ID_FUEL     and len(safe) >= 4: self.fuelRate     = round(_f32(safe), 2)
        elif can_id == _ID_THROTTLE and len(safe) >= 4: self.throttle     = round(_f32(safe), 2)
        elif can_id == _ID_TBL      and len(safe) >= 4: self.tbl          = round(_f32(safe), 2)
        elif can_id == _ID_SWY      and len(safe) >= 4: self.swy          = round(_f32(safe), 2)
        elif can_id == _ID_DRG      and len(safe) >= 4: self.drg          = round(_f32(safe), 2)
        elif can_id == _ID_ACC_X    and len(safe) >= 4: self.accX         = round(_f32(safe), 3)
        elif can_id == _ID_ACC_Y    and len(safe) >= 4: self.accY         = round(_f32(safe), 3)
        elif can_id == _ID_ACC_Z    and len(safe) >= 4: self.accZ         = round(_f32(safe), 3)

        hex_data = " ".join(f"{b:02X}" for b in safe)
        self._append_log(f"RX  ID=0x{can_id:03X}  [{len(safe)}]  {hex_data}")
        self._csv_write("RX", can_id, safe)

    @Slot(str)
    def _on_error_occurred(self, msg: str) -> None:
        self._append_log(f"ERR {msg}")

    @Slot(str)
    def _on_file_loaded(self, path: str) -> None:
        self._append_log(f"File loaded OK: {path}")

    @Slot(str)
    def _on_file_load_error(self, msg: str) -> None:
        self._append_log(f"File load FAILED: {msg}")

    @Slot(bool)
    def _on_connection_changed(self, connected: bool) -> None:
        self.isConnected = connected
        self._append_log(f"Connection: {'connected' if connected else 'disconnected'}")

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _csv_write(self, direction: str, can_id: int, data: list[int]) -> None:
        if not self._is_logging or self._csv_writer is None:
            return
        wall_time = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        hex_data  = " ".join(f"{b:02X}" for b in data)
        self._csv_writer.writerow([wall_time, direction, f"0x{can_id:03X}", len(data), hex_data])  # type: ignore[union-attr]
        self._csv_file.flush()  # type: ignore[union-attr]

    def _append_log(self, line: str) -> None:
        self.statusLog = (self._status_log + "\n" + line).lstrip("\n")
        self.logMessage.emit(line)
