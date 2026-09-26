Read agent.md to understand the project rules.
Task: Initialize the project structure and create the application entry point.
Constraints:
Create a basic ui/main.qml file with a simple empty Window so the app doesn't crash on startup.
In src/main.py, set up the QApplication, QQmlApplicationEngine, and the basic QThread structure.
Do NOT implement the CAN logic yet. Just set up the Qt environment, load ui/main.qml, and ensure the app runs.
After writing the code, execute uv run python src/main.py in the terminal to verify the window opens successfully. If it fails, read the error and fix it.