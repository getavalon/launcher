import QtQuick 2.7
import QtQuick.Controls 2.0

ToolBar {
    height: 30

    property bool inset: false

    background: Rectangle {
        color: inset ? "#333" : "transparent"
        border.color: inset ? "#555" : "#222"
        anchors.margins: 2

        Rectangle {
            anchors.fill: parent
            anchors.margins: 1
            color: "transparent"
            border.color: inset ? "#222" : "#555"
        }
    }
}