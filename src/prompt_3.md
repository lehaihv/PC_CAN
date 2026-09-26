Now we connect the backend to the main thread safely using the Bridge pattern.
Read agent.md, src/main.py, and src/can_worker.py.
Task: Create the QML Bridge and integrate the threading in the main entry point.
Constraints:
Create src/qml_bridge.py. It should be a QObject that holds a reference to the CanWorker. It needs a slot send_command(int, list) that calls the worker's send slot, and it must listen to the worker's signals and re-emit them to QML (e.g., logMessage(str)).
Update src/main.py:
Instantiate the CanWorker.
Create a QThread.
Move the CanWorker to the QThread using moveToThread().
Connect the thread's started signal to the worker's start_listening slot.
Instantiate the QmlBridge, passing the worker to it.
Expose the QmlBridge to the QML engine using rootContext().setContextProperty('bridge', bridge_instance).
Ensure that when the QApplication is about to quit, the worker's stop slot is called and the thread is safely terminated using quit() and wait().
Run uv run python src/main.py to ensure no threading warnings or crashes occur.