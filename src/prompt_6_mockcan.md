Context: Read agent.md, src/can_worker.py, and src/qml_bridge.py. We need to build the UI without the physical PEAK-USB adapter.
Task: Create a MockCanWorker that is a drop-in replacement for CanWorker, and update main.py to switch between them using an environment variable.
Constraints for src/mock_can_worker.py:
Create a MockCanWorker(QObject) class that has the exact same signals and slots as CanWorker (defined in can_worker.py).
CRITICAL: Do NOT use time.sleep() or blocking loops. Use QTimer for all periodic operations to keep the thread responsive.
Implement realistic simulated behaviors:
start_listening: Start a QTimer that fires every 500ms. Each tick should emit message_received with simulated CAN data.
Simulate Motor RPM: Start at 0, randomly accelerate/decelerate between 0-5000 RPM with smooth transitions.
Simulate Temperature: Start at 25°C, slowly drift up to 80°C over time, then cool down. Add small random noise.
Simulate Voltage: Hover around 12.6V with ±0.2V noise.
Every 20 seconds, emit an error_occurred signal with a message like "Simulated bus timeout" to test error handling.
send_message: Just log the sent data to the console and emit a message_received echo after a 100ms delay (simulating loopback).
stop: Stop all timers and emit a final "Mock worker stopped" log message.
Add full type hints.
Constraints for src/main.py update:
Check the environment variable USE_MOCK (default to "1" if not set).
If USE_MOCK=1, instantiate MockCanWorker. Otherwise, instantiate CanWorker.
The rest of the threading and bridge setup remains identical.
Print to the console which worker is being used on startup.
Execution: Run uv run python src/main.py and verify that simulated data appears in the UI every 500ms. Then run USE_MOCK=0 uv run python src/main.py to verify it tries to use the real hardware (it will likely fail to connect, which is expected if the adapter isn't plugged in).

# Prompt for File Loading Simulation:
"Update MockCanWorker to handle file loading. When load_file(path) is called, simulate a 2-second delay using QTimer.singleShot, then emit a file_loaded signal with the filename. 10% of the time, emit a file_load_error signal to test error handling."

# Prompt for Connection Simulation:
"Add a simulate_disconnect slot to MockCanWorker that stops the timer and emits connection_changed(False). Add a simulate_reconnect slot that restarts it. Expose these through the QmlBridge so I can add test buttons to the UI."

# Prompt for Data Logging:
"Make MockCanWorker write all simulated CAN messages to a CSV file (mock_can_log.csv) so I can replay them later for consistent testing."

# Scenario 1: Building the UI on a laptop without hardware
``` bash
USE_MOCK=1 uv run python src/main.py
```
# Scenario 2: Real hardware testing
```   
# bash
USE_MOCK=0 uv run python src/main.py
```

