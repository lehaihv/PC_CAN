import QtQuick
import QtQuick.Layouts

// Reusable metric card.
// Properties: title (string), value (var), unit (string)
Rectangle {
    id: root

    property string title: "Title"
    property var    value: 0
    property string unit:  ""

    color:        "#2b2b2b"
    radius:       8
    border.color: "#333333"
    border.width: 1

    implicitWidth:  180
    implicitHeight: 120

    ColumnLayout {
        anchors.fill:    parent
        anchors.margins: 16
        spacing:         4

        // Title
        Text {
            Layout.fillWidth: true
            text:             root.title
            color:            "#9e9e9e"
            font.pixelSize:   12
            font.weight:      Font.Medium
            elide:            Text.ElideRight
        }

        // Value — large, accent-coloured
        Text {
            Layout.fillWidth:  true
            Layout.fillHeight: true
            text:              root.value
            color:             "#00a8e8"
            font.pixelSize:    36
            font.weight:       Font.Bold
            verticalAlignment: Text.AlignVCenter
            elide:             Text.ElideRight
        }

        // Unit
        Text {
            Layout.fillWidth: true
            text:             root.unit
            color:            "#757575"
            font.pixelSize:   11
        }
    }
}
