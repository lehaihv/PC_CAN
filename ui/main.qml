import QtQuick
import QtQuick.Window
import QtQuick.Layouts
import QtQuick.Controls
import QtQuick.Controls.Material
import QtQuick.Dialogs
import "components"

Window {
    id:           root
    width:        1100
    height:       680
    minimumWidth: 800
    minimumHeight: 560
    title:        "PC CAN Monitor"
    visible:      true

    Material.theme:   Material.Dark
    Material.accent:  "#00a8e8"

    // Window background
    color: "#1a1a1a"

    // ── File dialog ───────────────────────────────────────────────────
    FileDialog {
        id:       fileDialog
        title:    "Select CAN Configuration"
        onAccepted: bridge.loadFile(fileDialog.selectedFile)
    }

    // ── Root layout: Sidebar | Main area ─────────────────────────────
    RowLayout {
        anchors.fill: parent
        spacing:      0

        // ── Sidebar ───────────────────────────────────────────────────
        Sidebar {
            id:                 sidebar
            Layout.fillHeight:  true
            Layout.preferredWidth: 250

            isRunning:   bridge.isRunning
            configModel: bridge.selectedConfig !== ""
                             ? [bridge.selectedConfig]
                             : ["No config loaded"]

            onLoadFileRequested: fileDialog.open()
            onStartRequested:    bridge.startAcquisition()
            onStopRequested:     bridge.stopAcquisition()
        }

        // ── Thin divider ──────────────────────────────────────────────
        Rectangle {
            Layout.fillHeight: true
            width:             1
            color:             "#333333"
        }

        // ── Main content area ─────────────────────────────────────────
        ColumnLayout {
            Layout.fillWidth:  true
            Layout.fillHeight: true
            Layout.margins:    16
            spacing:           12

            // ── Header row ────────────────────────────────────────────
            RowLayout {
                Layout.fillWidth: true
                spacing:          12

                Text {
                    text:           "Dashboard"
                    color:          "#ffffff"
                    font.pixelSize: 22
                    font.weight:    Font.Bold
                }

                Item { Layout.fillWidth: true }

                // Connection status dot + label
                Row {
                    spacing: 6

                    Rectangle {
                        width:  10
                        height: 10
                        radius: 5
                        anchors.verticalCenter: parent.verticalCenter
                        color: bridge.isConnected ? "#4caf50" : "#f44336"

                        // Subtle glow when connected
                        layer.enabled: bridge.isConnected
                        layer.effect: null  // placeholder — no extra dependency needed
                    }

                    Text {
                        text:  bridge.isConnected ? "Connected" : "Disconnected"
                        color: bridge.isConnected ? "#4caf50" : "#f44336"
                        font.pixelSize: 13
                        anchors.verticalCenter: parent.verticalCenter
                    }
                }
            }

            // ── Divider ───────────────────────────────────────────────
            Rectangle {
                Layout.fillWidth: true
                height:           1
                color:            "#333333"
            }

            // ── Metric cards grid (2 columns) ─────────────────────────
            GridLayout {
                Layout.fillWidth: true
                columns:          2
                columnSpacing:    12
                rowSpacing:       12

                DataCard {
                    Layout.fillWidth: true
                    title:            "Motor RPM"
                    value:            bridge.motorRpm
                    unit:             "RPM"
                }

                DataCard {
                    Layout.fillWidth: true
                    title:            "Temperature"
                    value:            bridge.temperature.toFixed(1)
                    unit:             "°C"
                }

                DataCard {
                    Layout.fillWidth: true
                    title:            "Voltage"
                    value:            bridge.voltage.toFixed(2)
                    unit:             "V"
                }

                DataCard {
                    Layout.fillWidth: true
                    title:            "Current"
                    value:            "—"
                    unit:             "A"
                }
            }

            // ── Send frame panel ──────────────────────────────────────
            SendFrame {
                Layout.fillWidth: true
                onFrameSend: (canId, data) => bridge.send_command(canId, data)
            }

            // ── Log area ──────────────────────────────────────────────
            Text {
                text:           "CAN LOG"
                color:          "#9e9e9e"
                font.pixelSize: 10
                font.weight:    Font.Medium
                font.letterSpacing: 1.2
            }

            Rectangle {
                Layout.fillWidth:  true
                Layout.fillHeight: true
                color:             "#2b2b2b"
                radius:            8
                border.color:      "#333333"
                border.width:      1

                ScrollView {
                    anchors.fill:    parent
                    anchors.margins: 1   // keep inside the border radius
                    clip:            true

                    TextArea {
                        id:          logArea
                        readOnly:    true
                        text:        bridge.statusLog
                        color:       "#b0b0b0"
                        font.family: "Monospace"
                        font.pixelSize: 12
                        wrapMode:    TextArea.Wrap
                        background:  null   // inherit from parent Rectangle

                        // Auto-scroll to bottom when new content arrives
                        onTextChanged: {
                            // Move cursor to end to trigger scroll
                            cursorPosition = length
                        }
                    }
                }
            }
        }
    }
}
