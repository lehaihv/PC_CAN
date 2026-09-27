Read agent.md.
Task: Implement the hardware backend in src/can_worker.py.
Constraints:
Create a CanWorker(QObject) class.
It must have a start_listening slot that initializes python-can with bustype='pcan', channel='PCAN_USBBUS1', bitrate=500000.
It must run a continuous loop to read messages. CRITICAL: Use a timeout (e.g., 0.1s) on the bus.recv() call so the thread can check for a stop flag and exit gracefully.
Define a message_received PySide6 Signal that emits the CAN ID (int) and data (list of ints).
Define a send_message slot that takes an ID (int) and data (list of ints) and sends it via the bus.
Handle can.CanError and emit an error_occurred(str) signal if initialization or sending fails.
Include a stop slot to cleanly shut down the bus and exit the loop.
Add strict Python type hints to all methods.