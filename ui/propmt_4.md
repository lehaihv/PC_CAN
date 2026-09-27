Context: Read agent.md. We are now building the QML frontend.
Task: Create a modern, dark-mode dashboard UI. To keep the code clean, you must break the UI into reusable QML components.
1. Data Contract (Assume these exist on the bridge context property):
Properties: isConnected (bool), isRunning (bool), selectedConfig (string), motorRpm (int), temperature (float), statusLog (string).
Functions: startAcquisition(), stopAcquisition(), requestLoadFile().
2. Component Extraction:
Create ui/components/DataCard.qml: A reusable card with a title (top), a large value (center), and a unit label (bottom). It should accept title, value, and unit as properties.
Create ui/components/Sidebar.qml: Contains the ComboBox for configuration, the "Load File" button, and the Start/Stop buttons.
3. Main Layout (ui/main.qml):
Use a RowLayout for the main structure: The Sidebar on the left (fixed width, e.g., 250px), and the main dashboard area on the right.
Header: At the top of the main area, add a title and a connection status indicator (a small Circle that is green if bridge.isConnected is true, red otherwise).
Dashboard Grid: Use a GridLayout (2 columns) in the main area to display multiple DataCard components (e.g., Motor RPM, Temperature, Voltage). Bind their value properties to the bridge properties.
Log Area: At the bottom of the main area, add a read-only TextArea bound to bridge.statusLog to show live CAN messages.
4. Dialogs:
Include a FileDialog in main.qml. When the "Load File" button in the sidebar is clicked, open the dialog. When a file is accepted, call bridge.loadFile(dialog.selectedFile).
5. Styling & Modern Look (CRITICAL):
Use Qt Quick Controls 2 with the Material theme (Dark).
Do NOT use absolute x and y positioning. Use Layout items (RowLayout, ColumnLayout, GridLayout) exclusively.
Use consistent spacing: Layout.margins: 16 for main areas, spacing: 12 inside layouts.
For DataCard, use a Rectangle with radius: 8, a subtle border (border.color: "#333333"), and a slightly lighter background than the main window (color: "#2b2b2b").
Use a modern accent color (e.g., #00a8e8 cyan) for active buttons and highlights.
Execution: Write the code for the components first, then main.qml. Ensure all property bindings to the bridge are correctly mapped.