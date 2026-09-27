import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import QtQuick.Controls.Material

// CAN frame transmit panel.
//
// Signal
//   frameSend(int canId, var data)
//
// Wire in parent: onFrameSend: (canId, data) => bridge.send_command(canId, data)

Rectangle {
    id: root

    signal frameSend(int canId, var data)

    color:        "#2b2b2b"
    radius:       8
    border.color: "#333333"
    border.width: 1

    implicitHeight: sendLayout.implicitHeight + 24

    // ── Pure JS helpers (no property dependencies inside) ─────────────

    function parseId(t) {
        var s = t.trim()
        var n = parseInt(s, s.toLowerCase().startsWith("0x") ? 16 : 10)
        return (isNaN(n) || n < 0 || n > 0x7FF) ? -1 : n
    }

    // Returns int[] on success, null on any error.
    function parseData(t) {
        var s = t.trim()
        if (s === "") return []           // empty = 0 bytes, valid
        var parts = s.split(/[\s,]+/)
        var out = []
        for (var i = 0; i < parts.length; i++) {
            var tok = parts[i]
            if (tok === "") continue
            var b = parseInt(tok, 16)
            if (isNaN(b) || b < 0 || b > 255) return null
            out.push(b)
        }
        return out.length > 8 ? null : out
    }

    // ── Reactive validation — each binding explicitly reads the text
    //    fields so QML knows to re-evaluate when they change ───────────

    property bool idOk: {
        var _ = idField.text          // explicit dependency
        return parseId(idField.text) !== -1
    }

    property bool dataOk: {
        var _ = dataField.text        // explicit dependency
        return parseData(dataField.text) !== null
    }

    property bool canSend: idOk && dataOk

    // ── Layout ────────────────────────────────────────────────────────
    ColumnLayout {
        id:      sendLayout
        anchors { left: parent.left; right: parent.right; top: parent.top; margins: 12 }
        spacing: 8

        Text {
            text:               "SEND FRAME"
            color:              "#9e9e9e"
            font.pixelSize:     10
            font.weight:        Font.Medium
            font.letterSpacing: 1.2
        }

        RowLayout {
            Layout.fillWidth: true
            spacing:          8

            // ── CAN ID ────────────────────────────────────────────────
            ColumnLayout {
                spacing: 4

                Text {
                    text:           "CAN ID (hex)"
                    color:          "#9e9e9e"
                    font.pixelSize: 11
                }

                TextField {
                    id:                    idField
                    text:                  "0x200"
                    Layout.preferredWidth: 110
                    color:                 "#ffffff"
                    font.family:           "Monospace"
                    font.pixelSize:        13
                    selectByMouse:         true

                    Material.accent:         root.idOk ? "#00a8e8" : "#c62828"
                    Material.containerStyle: Material.Outlined
                }
            }

            // ── Data bytes ────────────────────────────────────────────
            ColumnLayout {
                spacing:          4
                Layout.fillWidth: true

                Text {
                    text:           "Data bytes (hex, space-separated, 0–8)"
                    color:          "#9e9e9e"
                    font.pixelSize: 11
                }

                TextField {
                    id:               dataField
                    Layout.fillWidth: true
                    color:            "#ffffff"
                    font.family:      "Monospace"
                    font.pixelSize:   13
                    selectByMouse:    true

                    Material.accent:         root.dataOk ? "#00a8e8" : "#c62828"
                    Material.containerStyle: Material.Outlined

                    Keys.onReturnPressed: if (root.canSend) sendBtn.clicked()
                    Keys.onEnterPressed:  if (root.canSend) sendBtn.clicked()
                }
            }

            // ── Send button ───────────────────────────────────────────
            ColumnLayout {
                spacing: 4

                Text { text: " "; font.pixelSize: 11; color: "transparent" }

                Button {
                    id:      sendBtn
                    text:    "Send"
                    enabled: root.canSend

                    Material.background: root.canSend ? "#00a8e8" : "#383838"
                    Material.foreground: "#ffffff"

                    onClicked: {
                        var id   = root.parseId(idField.text)
                        var data = root.parseData(dataField.text)
                        root.frameSend(id, data)
                        flashTimer.restart()
                    }
                }
            }
        }

        // Status / validation line
        Text {
            Layout.fillWidth: true
            elide:            Text.ElideRight

            text: {
                // read both fields to keep this binding live
                var idText   = idField.text
                var dataText = dataField.text

                if (!root.idOk)
                    return "\u26A0  Invalid CAN ID — enter 0x000 to 0x7FF"
                if (!root.dataOk)
                    return "\u26A0  Invalid data — up to 8 hex bytes (e.g. DE AD BE EF)"

                var d = root.parseData(dataText)
                return "\u2713  ID 0x" + root.parseId(idText).toString(16).toUpperCase()
                       + "  [" + d.length + " byte" + (d.length !== 1 ? "s" : "") + "]"
            }
            color:          root.canSend ? "#4caf50" : "#ef9a9a"
            font.pixelSize: 11
        }
    }

    // Border flash on send
    Timer {
        id:          flashTimer
        interval:    350
        onTriggered: root.border.color = "#333333"
    }
    onFrameSend: root.border.color = "#00a8e8"
}
