import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import QtQuick.Controls.Material

// Sidebar panel: config selector, Load File, Start/Stop.
//
// Signals
//   loadFileRequested()   – user clicked "Load File"
//   startRequested()      – user clicked "Start"
//   stopRequested()       – user clicked "Stop"
//
// Properties (bind from parent)
//   isRunning   (bool)  – drives Start/Stop button state
//   configModel (list)  – ComboBox model, defaults to a placeholder list

Rectangle {
    id: root

    // ------------------------------------------------------------------
    // Public API
    // ------------------------------------------------------------------
    signal loadFileRequested()
    signal startRequested()
    signal stopRequested()
    signal logStartRequested(string path)
    signal logStopRequested()

    property bool   isRunning:   false
    property bool   isLogging:   false
    property string logFilePath: ""
    property var    configModel: ["No configs loaded"]

    // ------------------------------------------------------------------
    // Appearance
    // ------------------------------------------------------------------
    color: "#1e1e1e"

    ColumnLayout {
        anchors.fill:    parent
        anchors.margins: 16
        spacing:         12

        // ── App brand ─────────────────────────────────────────────────
        Text {
            text:           "PC CAN"
            color:          "#ffffff"
            font.pixelSize: 20
            font.weight:    Font.Bold
        }

        Rectangle { color: "#333333"; Layout.fillWidth: true; height: 1 }

        // ── Section label ─────────────────────────────────────────────
        Text {
            text:           "CONFIGURATION"
            color:          "#9e9e9e"
            font.pixelSize: 10
            font.weight:    Font.Medium
            font.letterSpacing: 1.2
        }

        // ── Config selector ───────────────────────────────────────────
        ComboBox {
            id:               configCombo
            Layout.fillWidth: true
            model:            root.configModel

            Material.foreground: "#ffffff"
            Material.accent:     "#00a8e8"

            background: Rectangle {
                color:        "#2b2b2b"
                radius:       6
                border.color: "#444444"
                border.width: 1
            }

            contentItem: Text {
                leftPadding: 12
                text:        configCombo.displayText
                color:       "#ffffff"
                font:        configCombo.font
                verticalAlignment: Text.AlignVCenter
                elide:       Text.ElideRight
            }
        }

        // ── Load File button ──────────────────────────────────────────
        Button {
            Layout.fillWidth: true
            text:             "Load File…"

            Material.background: "#2b2b2b"
            Material.foreground: "#00a8e8"

            onClicked: root.loadFileRequested()
        }

        Rectangle { color: "#333333"; Layout.fillWidth: true; height: 1 }

        // ── Section label ─────────────────────────────────────────────
        Text {
            text:           "ACQUISITION"
            color:          "#9e9e9e"
            font.pixelSize: 10
            font.weight:    Font.Medium
            font.letterSpacing: 1.2
        }

        // ── Start button ──────────────────────────────────────────────
        Button {
            Layout.fillWidth: true
            text:             "Start"
            enabled:          !root.isRunning

            Material.background: root.isRunning ? "#1a3a1a" : "#00a8e8"
            Material.foreground: root.isRunning ? "#4caf50" : "#ffffff"

            onClicked: root.startRequested()
        }

        // ── Stop button ───────────────────────────────────────────────
        Button {
            Layout.fillWidth: true
            text:             "Stop"
            enabled:          root.isRunning

            Material.background: root.isRunning ? "#c62828" : "#2b2b2b"
            Material.foreground: "#ffffff"

            onClicked: root.stopRequested()
        }

        Rectangle { color: "#333333"; Layout.fillWidth: true; height: 1 }

        // ── CSV Logging card ──────────────────────────────────────────
        LoggingCard {
            Layout.fillWidth: true
            isLogging:        root.isLogging
            logFilePath:      root.logFilePath

            onStartRequested: (path) => root.logStartRequested(path)
            onStopRequested:  root.logStopRequested()
        }

        // ── Spacer ────────────────────────────────────────────────────
        Item { Layout.fillHeight: true }

        // ── Version footer ────────────────────────────────────────────
        Text {
            text:           "v0.1.0"
            color:          "#555555"
            font.pixelSize: 10
        }
    }
}
