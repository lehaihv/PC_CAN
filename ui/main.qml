import QtQuick
import QtQuick.Window
import QtQuick.Layouts
import QtQuick.Controls
import QtQuick.Controls.Material
import QtQuick.Dialogs
import "components"

Window {
    id:            root
    width:         1300
    height:        780
    minimumWidth:  1000
    minimumHeight: 660
    title:         "PC CAN Monitor"
    visible:       true

    Material.theme:  Material.Dark
    Material.accent: "#00a8e8"
    color:           "#1a1a1a"

    // ── Config file dialog ────────────────────────────────────────────
    FileDialog {
        id:         fileDialog
        title:      "Select CAN Configuration"
        onAccepted: bridge.loadFile(fileDialog.selectedFile)
    }

    // ── Root layout: Sidebar | Main area ─────────────────────────────
    RowLayout {
        anchors.fill: parent
        spacing:      0

        // ── Sidebar ───────────────────────────────────────────────────
        Sidebar {
            id:                    sidebar
            Layout.fillHeight:     true
            Layout.preferredWidth: 250

            isRunning:   bridge.isRunning
            isLogging:   bridge.isLogging
            logFilePath: bridge.logFilePath
            configModel: bridge.selectedConfig !== ""
                             ? [bridge.selectedConfig]
                             : ["No config loaded"]

            onLoadFileRequested:         fileDialog.open()
            onStartRequested:            bridge.startAcquisition()
            onStopRequested:             bridge.stopAcquisition()
            onLogStartRequested: (path) => bridge.startLogging(path)
            onLogStopRequested:          bridge.stopLogging()
        }

        Rectangle { Layout.fillHeight: true; width: 1; color: "#333333" }

        // ── Main content ──────────────────────────────────────────────
        ColumnLayout {
            Layout.fillWidth:  true
            Layout.fillHeight: true
            Layout.margins:    16
            spacing:           12

            // ── Header ────────────────────────────────────────────────
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

                Row {
                    spacing: 6
                    Rectangle {
                        width: 10; height: 10; radius: 5
                        anchors.verticalCenter: parent.verticalCenter
                        color: bridge.isConnected ? "#4caf50" : "#f44336"
                    }
                    Text {
                        text:  bridge.isConnected ? "Connected" : "Disconnected"
                        color: bridge.isConnected ? "#4caf50" : "#f44336"
                        font.pixelSize: 13
                        anchors.verticalCenter: parent.verticalCenter
                    }
                }
            }

            Rectangle { Layout.fillWidth: true; height: 1; color: "#333333" }

            // ── Metric grid — 6 columns × 2 rows = 12 cards ──────────
            GridLayout {
                Layout.fillWidth: true
                columns:          6
                columnSpacing:    12
                rowSpacing:       12

                // Row 1
                DataCard { Layout.fillWidth: true; title: "Motor RPM";     value: bridge.motorRpm;                unit: "RPM"  }
                DataCard { Layout.fillWidth: true; title: "Vehicle Speed"; value: bridge.vehicleSpeed;            unit: "km/h" }
                DataCard { Layout.fillWidth: true; title: "Throttle";      value: bridge.throttle.toFixed(1);     unit: "%"    }
                DataCard { Layout.fillWidth: true; title: "Voltage";       value: bridge.voltage.toFixed(2);      unit: "V"    }
                DataCard { Layout.fillWidth: true; title: "Fuel Rate";     value: bridge.fuelRate.toFixed(2);     unit: "L/h"  }
                DataCard { Layout.fillWidth: true; title: "Temperature";   value: bridge.temperature.toFixed(1);  unit: "°C"   }

                // Row 2
                DataCard { Layout.fillWidth: true; title: "TBL";           value: bridge.tbl.toFixed(2);          unit: "kg"   }
                DataCard { Layout.fillWidth: true; title: "SWY";           value: bridge.swy.toFixed(2);          unit: "kg"   }
                DataCard { Layout.fillWidth: true; title: "DRG";           value: bridge.drg.toFixed(2);          unit: "kg"   }
                DataCard { Layout.fillWidth: true; title: "ACC_X";         value: bridge.accX.toFixed(3);         unit: "g"    }
                DataCard { Layout.fillWidth: true; title: "ACC_Y";         value: bridge.accY.toFixed(3);         unit: "g"    }
                DataCard { Layout.fillWidth: true; title: "ACC_Z";         value: bridge.accZ.toFixed(3);         unit: "g"    }
            }

            // ── Send frame ────────────────────────────────────────────
            SendFrame {
                Layout.fillWidth: true
                onFrameSend: (canId, data) => bridge.send_command(canId, data)
            }

            // ── CAN log ───────────────────────────────────────────────
            Text {
                text: "CAN LOG"; color: "#9e9e9e"
                font.pixelSize: 10; font.weight: Font.Medium; font.letterSpacing: 1.2
            }

            Rectangle {
                Layout.fillWidth:  true
                Layout.fillHeight: true
                color:        "#2b2b2b"
                radius:       8
                border.color: "#333333"
                border.width: 1

                ScrollView {
                    anchors.fill:    parent
                    anchors.margins: 1
                    clip:            true

                    TextArea {
                        id:          logArea
                        readOnly:    true
                        text:        bridge.statusLog
                        color:       "#b0b0b0"
                        font.family: "Monospace"
                        font.pixelSize: 12
                        wrapMode:    TextArea.Wrap
                        background:  null
                        onTextChanged: cursorPosition = length
                    }
                }
            }
        }
    }
}
