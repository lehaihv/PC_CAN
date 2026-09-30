"""
Application entry point.

Worker selection via environment variable:
  USE_MOCK=1 (default)  →  MockCanWorker  — synthetic data, no hardware needed
  USE_MOCK=0            →  CanWorker      — real PEAK-USB adapter required

Usage:
  uv run python src/main.py           # mock mode (default)
  USE_MOCK=0 uv run python src/main.py  # real hardware
"""

import os
import sys
from pathlib import Path

from PySide6.QtCore import QThread
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle

from can_worker import CanWorker
from mock_can_worker import MockCanWorker
from qml_bridge import QmlBridge, AnyWorker


def main() -> None:
    # Material style MUST be set before QGuiApplication is constructed
    QQuickStyle.setStyle("Material")

    app = QGuiApplication(sys.argv)

    use_mock: bool = os.environ.get("USE_MOCK", "1") == "1"

    # ------------------------------------------------------------------
    # 1. Instantiate the appropriate worker
    # ------------------------------------------------------------------
    worker: AnyWorker
    if use_mock:
        worker = MockCanWorker()
        print("[main] Worker: MockCanWorker (USE_MOCK=1 — synthetic data)")
    else:
        worker = CanWorker()
        print("[main] Worker: CanWorker    (USE_MOCK=0 — real PCAN hardware)")

    # ------------------------------------------------------------------
    # 2. Move worker to a dedicated QThread
    #    MockCanWorker uses QTimer, which is also perfectly happy running
    #    inside a QThread — so the threading setup is identical for both.
    # ------------------------------------------------------------------
    can_thread = QThread()
    worker.moveToThread(can_thread)
    can_thread.started.connect(worker.start_listening)

    # ------------------------------------------------------------------
    # 3. Bridge (always stays on the GUI thread)
    # ------------------------------------------------------------------
    bridge = QmlBridge(worker=worker)

    # ------------------------------------------------------------------
    # 4. Clean teardown on quit
    # ------------------------------------------------------------------
    def _on_about_to_quit() -> None:
        worker.stop()
        bridge.stopLogging()   # flush CSV if logging was active
        can_thread.quit()
        can_thread.wait()

    app.aboutToQuit.connect(_on_about_to_quit)

    # ------------------------------------------------------------------
    # 5. Load QML and expose the bridge
    # ------------------------------------------------------------------
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("bridge", bridge)

    qml_file = Path(__file__).parent.parent / "ui" / "main.qml"
    engine.load(qml_file)

    if not engine.rootObjects():
        print("ERROR: Failed to load QML file.", file=sys.stderr)
        sys.exit(1)

    # ------------------------------------------------------------------
    # 6. Start the worker thread (QML is ready, bridge is registered)
    # ------------------------------------------------------------------
    can_thread.start()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
