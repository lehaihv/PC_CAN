# Project Context
You are an expert Python and Qt/QML developer. We are building a desktop GUI application that communicates with an ESP32-S3 via CAN bus using a PEAK-USB adapter and the `python-can` library.

# Strict Architectural Rules
1. **UI Framework**: PySide6 with QML (Qt Quick). NEVER use QtWidgets.
2. **Threading (CRITICAL)**: ALL `python-can` operations (reading/writing to the bus) MUST happen in a dedicated `QThread`. The main GUI thread must NEVER block. Use `QObject.moveToThread()` and `pyqtSignal` for communication.
3. **State Management**: QML UI elements must bind to Python signals. Do not write complex business logic in QML JavaScript.
4. **CAN Interface**: Use `python-can` with `bustype='pcan'`. Handle `can.CanError` gracefully.

# Workflow Rules for the Agent
- Before writing code, briefly state your plan in 1-2 sentences.
- When modifying existing files, show the full updated file or clear, precise diffs.
- If a task is complex, break it down and ask for my confirmation before writing the code.
- Always write type hints for Python functions.

# Environment & Dependency Rules (CRITICAL)
- **Package Manager:** We use `uv`. NEVER use `pip`, `pip install`, or `python -m venv`.
- **Adding Dependencies:** Use `uv add <package_name>` to install new libraries. This automatically updates `pyproject.toml` and `uv.lock`.
- **Running Code:** NEVER manually activate the virtual environment. Always use `uv run <command>` to execute Python scripts, tests, or linters. 
  - Example: `uv run python src/main.py`
  - Example: `uv run pytest tests/`
