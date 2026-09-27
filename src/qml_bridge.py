"""
QML Bridge — thread-safe adapter between QML and the CAN worker.

Accepts either CanWorker or MockCanWorker; both share the same public
signal/slot interface so this class needs no conditional logic.
"""

import struct
from typing import Union, Optional

from PySide6.QtCore import Property, QObject, Signal, Slot

from can_worker import CanWorker
from mock_can_worker import MockCanWorker

# Type alias used in __init__ signature
AnyWorker = Union[CanWorker, MockCanWorker]

# ---------------------------------------------------------------------------
# CAN ID → property mapping (agreed protocol with ESP32-S3 firmware)
# ---------------------------------------------------------------------------
_CAN_ID_MOTOR_RPM:   int = 0x101  # data[0:2] big-endian uint16
_CAN_ID_TEMPERATURE: int = 0x102  # data[0:4] big-endian float32 °C
_CAN_ID_VOLTAGE:     int = 0x103  # data[0:4] big-endian float32 V


class QmlBridge(QObject):
    """
    Thread-safe bridge between the QML UI and the CAN worker backend.

    Lives on the main (GUI) thread.  Qt uses queued connections for all
    worker signals, so cross-thread delivery is handled automatically.

    QML-exposed properties
    ----------------------
    isConnected   : bool
    isRunning     : bool
    selectedConfig: str
    motorRpm      : int
    temperature   : float
    voltage       : float
    statusLog     : str

    QML-exposed slots
    -----------------
    startAcquisition()
    stopAcquisition()
    requestLoadFile()
    loadFile(file_url: str)
    send_command(can_id: int, data: list[int])
    simulateDisconnect()   – mock only; no-op on real worker
    simulateReconnect()    – mock only; no-op on real worker
    """

    # ── @Property notification signals ────────────────────────────────
    isConnectedChanged:    Signal = Signal()
    isRunningChanged:      Signal = Signal()
    selectedConfigChanged: Signal = Signal()
    motorRpmChanged:       Signal = Signal()
    temperatureChanged:    Signal = Signal()
    voltageChanged:        Signal = Signal()
    statusLogChanged:      Signal = Signal()

    # ── General-purpose signal (not a property notification) ───────────
    logMessage: Signal = Signal(str)

    def __init__(
        self,
        worker: AnyWorker,
        parent: Optional[QObject] = None,
    ) -> None:
        super().__init__(parent)
        self._worker: AnyWorker = worker
        self._is_mock: bool = isinstance(worker, MockCanWorker)

        # Backing fields for QML properties
        self._is_connected:    bool  = False
        self._is_running:      bool  = False
        self._selected_config: str   = ""
        self._motor_rpm:       int   = 0
        self._temperature:     float = 0.0
        self._voltage:         float = 0.0
        self._status_log:      str   = ""

        # ── Connect core worker signals ────────────────────────────────
        self._worker.message_received.connect(self._on_message_received)
        self._worker.error_occurred.connect(self._on_error_occurred)

        # ── Connect mock-only signals (if running in mock mode) ────────
        if self._is_mock:
            mock = self._worker  # type: ignore[assignment]
            mock.file_loaded.connect(self._on_file_loaded)
            mock.file_load_error.connect(self._on_file_load_error)
            mock.connection_changed.connect(self._on_connection_changed)

    # ------------------------------------------------------------------
    # QML-bindable properties
    # ------------------------------------------------------------------

    @Property(bool, notify=isConnectedChanged)
    def isConnected(self) -> bool:
        return self._is_connected

    @isConnected.setter
    def isConnected(self, value: bool) -> None:
        if self._is_connected != value:
            self._is_connected = value
            self.isConnectedChanged.emit()

    @Property(bool, notify=isRunningChanged)
    def isRunning(self) -> bool:
        return self._is_running

    @isRunning.setter
    def isRunning(self, value: bool) -> None:
        if self._is_running != value:
            self._is_running = value
            self.isRunningChanged.emit()

    @Property(str, notify=selectedConfigChanged)
    def selectedConfig(self) -> str:
        return self._selected_config

    @selectedConfig.setter
    def selectedConfig(self, value: str) -> None:
        if self._selected_config != value:
            self._selected_config = value
            self.selectedConfigChanged.emit()

    @Property(int, notify=motorRpmChanged)
    def motorRpm(self) -> int:
        return self._motor_rpm

    @motorRpm.setter
    def motorRpm(self, value: int) -> None:
        if self._motor_rpm != value:
            self._motor_rpm = value
            self.motorRpmChanged.emit()

    @Property(float, notify=temperatureChanged)
    def temperature(self) -> float:
        return self._temperature

    @temperature.setter
    def temperature(self, value: float) -> None:
        if self._temperature != value:
            self._temperature = value
            self.temperatureChanged.emit()

    @Property(float, notify=voltageChanged)
    def voltage(self) -> float:
        return self._voltage

    @voltage.setter
    def voltage(self, value: float) -> None:
        if self._voltage != value:
            self._voltage = value
            self.voltageChanged.emit()

    @Property(str, notify=statusLogChanged)
    def statusLog(self) -> str:
        return self._status_log

    @statusLog.setter
    def statusLog(self, value: str) -> None:
        if self._status_log != value:
            self._status_log = value
            self.statusLogChanged.emit()

    # ------------------------------------------------------------------
    # Slots callable from QML
    # ------------------------------------------------------------------

    @Slot()
    def startAcquisition(self) -> None:
        """Mark the bus as connected and running."""
        self.isConnected = True
        self.isRunning   = True
        self._append_log("Acquisition started.")

    @Slot()
    def stopAcquisition(self) -> None:
        """Pause acquisition (bus stays connected)."""
        self.isRunning = False
        self._append_log("Acquisition stopped.")

    @Slot()
    def requestLoadFile(self) -> None:
        """Placeholder — actual FileDialog lives in QML."""
        self._append_log("Load file requested.")

    @Slot(str)
    def loadFile(self, file_url: str) -> None:
        """Receive the file URL chosen by the QML FileDialog."""
        self._append_log(f"Config loading: {file_url}")
        self.selectedConfig = file_url
        # In mock mode, delegate to the simulated loader
        if self._is_mock:
            self._worker.load_file(file_url)  # type: ignore[union-attr]

    @Slot(int, list)
    def send_command(self, can_id: int, data: list[int]) -> None:
        """Forward a raw CAN frame to the worker (cross-thread safe)."""
        self._worker.send_message(can_id, data)

    @Slot()
    def simulateDisconnect(self) -> None:
        """Trigger a simulated bus disconnect (mock mode only)."""
        if self._is_mock:
            self._worker.simulate_disconnect()  # type: ignore[union-attr]
        else:
            self._append_log("simulateDisconnect: ignored (real hardware mode).")

    @Slot()
    def simulateReconnect(self) -> None:
        """Trigger a simulated bus reconnect (mock mode only)."""
        if self._is_mock:
            self._worker.simulate_reconnect()  # type: ignore[union-attr]
        else:
            self._append_log("simulateReconnect: ignored (real hardware mode).")

    # ------------------------------------------------------------------
    # Private — worker signal handlers (run on GUI thread)
    # ------------------------------------------------------------------

    @Slot(int, list)
    def _on_message_received(self, can_id: int, data: list[int]) -> None:
        """
        Decode incoming frame and update the matching property.

        0x101  Motor RPM   – bytes[0:2] big-endian uint16
        0x102  Temperature – bytes[0:4] big-endian float32
        0x103  Voltage     – bytes[0:4] big-endian float32
        """
        # Coerce to int — QML passes JS numbers as float
        safe: list[int] = [int(b) for b in data]

        if can_id == _CAN_ID_MOTOR_RPM and len(safe) >= 2:
            self.motorRpm = struct.unpack(">H", bytes(safe[:2]))[0]

        elif can_id == _CAN_ID_TEMPERATURE and len(safe) >= 4:
            self.temperature = round(
                struct.unpack(">f", bytes(safe[:4]))[0], 2
            )

        elif can_id == _CAN_ID_VOLTAGE and len(safe) >= 4:
            self.voltage = round(
                struct.unpack(">f", bytes(safe[:4]))[0], 3
            )

        hex_data = " ".join(f"{b:02X}" for b in safe)
        self._append_log(f"RX  ID=0x{can_id:03X}  [{len(safe)}]  {hex_data}")

    @Slot(str)
    def _on_error_occurred(self, message: str) -> None:
        self._append_log(f"ERR {message}")

    @Slot(str)
    def _on_file_loaded(self, path: str) -> None:
        self._append_log(f"File loaded OK: {path}")

    @Slot(str)
    def _on_file_load_error(self, message: str) -> None:
        self._append_log(f"File load FAILED: {message}")

    @Slot(bool)
    def _on_connection_changed(self, connected: bool) -> None:
        self.isConnected = connected
        state = "connected" if connected else "disconnected"
        self._append_log(f"Connection state changed: {state}")

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _append_log(self, line: str) -> None:
        """Append *line* to statusLog and emit logMessage."""
        self.statusLog = (self._status_log + "\n" + line).lstrip("\n")
        self.logMessage.emit(line)
