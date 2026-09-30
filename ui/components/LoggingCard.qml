import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import QtQuick.Controls.Material
import QtQuick.Dialogs

// CSV Logging control card for the sidebar.
//
// Properties (bind from parent):
//   isLogging   (bool) – reflects bridge.isLogging
//   logFilePath (str)  – reflects bridge.logFilePath
//
// Signals:
//   startRequested(string path) – user confirmed a file and clicked Start
//   stopRequested()             – user clicked Stop

Rectangle {
    id: root

    property bool   isLogging:   false
    property string logFilePath: ""

    signal startRequested(string path)
    signal stopRequested()

    color:        "#1e1e1e"   // matches sidebar background — no card box needed
    implicitHeight: cardCol.implicitHeight

    // ── Save-file dialog ──────────────────────────────────────────────
    FileDialog {
        id:           saveDialog
        title:        "Choose CSV log file location"
        fileMode:     FileDialog.SaveFile
        nameFilters:  ["CSV files (*.csv)", "All files (*)"]
        defaultSuffix: "csv"
        onAccepted:   pathField.text = saveDialog.selectedFile
    }

    ColumnLayout {
        id:       cardCol
        width:    parent.width
        spacing:  8

        // ── Section label ─────────────────────────────────────────────
        Text {
            text:               "CSV LOGGING"
            color:              "#9e9e9e"
            font.pixelSize:     10
            font.weight:        Font.Medium
            font.letterSpacing: 1.2
        }

        // ── Browse button ─────────────────────────────────────────────
        Button {
            Layout.fillWidth: true
            text:             "Save Log…"
            enabled:          !root.isLogging

            Material.background: "#2b2b2b"
            Material.foreground: "#00a8e8"

            onClicked: saveDialog.open()
        }

        // ── Selected path display ─────────────────────────────────────
        TextField {
            id:               pathField
            Layout.fillWidth: true
            text:             root.logFilePath
            color:            "#ffffff"
            font.pixelSize:   11
            font.family:      "Monospace"
            selectByMouse:    true
            enabled:          !root.isLogging

            Material.accent:         "#00a8e8"
            Material.containerStyle: Material.Outlined

            placeholderText: "No file selected"
        }

        // ── Start / Stop row ──────────────────────────────────────────
        RowLayout {
            Layout.fillWidth: true
            spacing:          6

            Button {
                Layout.fillWidth: true
                text:             "Start"
                enabled:          !root.isLogging && pathField.text.trim() !== ""

                Material.background: (!root.isLogging && pathField.text.trim() !== "")
                                         ? "#00a8e8" : "#2b2b2b"
                Material.foreground: "#ffffff"

                onClicked: root.startRequested(pathField.text.trim())
            }

            Button {
                Layout.fillWidth: true
                text:             "Stop"
                enabled:          root.isLogging

                Material.background: root.isLogging ? "#c62828" : "#2b2b2b"
                Material.foreground: "#ffffff"

                onClicked: root.stopRequested()
            }
        }

        // ── Status line ───────────────────────────────────────────────
        Row {
            spacing: 6

            Rectangle {
                width:   7
                height:  7
                radius:  4
                anchors.verticalCenter: parent.verticalCenter
                color: root.isLogging ? "#4caf50" : "#555555"
            }

            Text {
                text: root.isLogging
                          ? "Logging…"
                          : (root.logFilePath !== "" ? "Stopped" : "Idle")
                color: root.isLogging ? "#4caf50" : "#757575"
                font.pixelSize: 11
                anchors.verticalCenter: parent.verticalCenter
            }
        }
    }
}
