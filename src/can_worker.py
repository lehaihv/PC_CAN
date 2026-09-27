import threading
from typing import Optional

import can
from PySide6.QtCore import QObject, Signal, Slot


class CanWorker(QObject):
    """
    Hardware backend for CAN bus communication.

    Runs inside a dedicated QThread. All python-can I/O happens here;
    the GUI thread is never blocked.

    Signals
    -------
    message_received(int, list)
        Emitted for every incoming CAN frame.
        Arguments: arbitration_id, list of data bytes.
    error_occurred(str)
        Emitted when a can.CanError is caught during init or send.
    """

    message_received: Signal = Signal(int, list)
    error_occurred: Signal = Signal(str)

    # PCAN adapter configuration
    _BUSTYPE: str = "pcan"
    _CHANNEL: str = "PCAN_USBBUS1"
    _BITRATE: int = 500_000

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._bus: Optional[can.BusABC] = None
        self._stop_flag: threading.Event = threading.Event()

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    @Slot()
    def start_listening(self) -> None:
        """
        Initialize the PCAN bus and enter the receive loop.

        Must be called from within the worker's QThread (connect
        QThread.started to this slot before starting the thread).
        Blocks until stop() is called.
        """
        try:
            self._bus = can.interface.Bus(
                bustype=self._BUSTYPE,
                channel=self._CHANNEL,
                bitrate=self._BITRATE,
            )
        except (can.CanError, OSError) as exc:
            self.error_occurred.emit(
                f"CAN init failed ({self._CHANNEL} @ {self._BITRATE} bps): {exc}"
            )
            return

        self._stop_flag.clear()

        # Receive loop — 0.1 s timeout lets us poll the stop flag
        # without burning the CPU.
        while not self._stop_flag.is_set():
            try:
                msg: Optional[can.Message] = self._bus.recv(timeout=0.1)
            except can.CanError as exc:
                self.error_occurred.emit(f"CAN recv error: {exc}")
                break

            if msg is not None:
                self.message_received.emit(
                    msg.arbitration_id,
                    list(msg.data),
                )

        self._shutdown_bus()

    @Slot(int, list)
    def send_message(self, can_id: int, data: list[int]) -> None:
        """
        Send a CAN frame.

        Parameters
        ----------
        can_id:
            CAN arbitration ID (11-bit standard or 29-bit extended).
        data:
            Payload bytes (0–8 bytes).
        """
        if self._bus is None:
            self.error_occurred.emit(
                "send_message called before the bus was initialized."
            )
            return

        msg = can.Message(
            arbitration_id=can_id,
            data=data,
            is_extended_id=False,
        )
        try:
            self._bus.send(msg)
        except can.CanError as exc:
            self.error_occurred.emit(f"CAN send error (ID=0x{can_id:X}): {exc}")

    @Slot()
    def stop(self) -> None:
        """
        Signal the receive loop to exit and shut down the bus.

        Safe to call from any thread.
        """
        self._stop_flag.set()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _shutdown_bus(self) -> None:
        """Close the bus interface if it is open."""
        if self._bus is not None:
            try:
                self._bus.shutdown()
            except can.CanError:
                pass  # Already gone — nothing to do
            finally:
                self._bus = None
