Update the Python backend to match the QML's expectations:
Read agent.md, src/qml_bridge.py, and the new ui/main.qml.
Task: Update the Python QmlBridge to expose the exact properties and functions the QML frontend is expecting.
Constraints:
Add Property decorators (using @Property) for: isConnected, isRunning, selectedConfig, motorRpm, temperature, and statusLog.
Ensure that when the CanWorker emits a message_received signal, the bridge parses the data and updates the motorRpm or temperature properties, and emits the notify signal for that specific property so QML updates automatically.
Add the slots: startAcquisition(), stopAcquisition(), and requestLoadFile().
Run uv run python src/main.py to verify the app launches and the UI updates when the mock worker emits data.