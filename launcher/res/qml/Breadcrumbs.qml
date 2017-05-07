import QtQuick 2.6
import QtQuick.Controls 2.1


Item {
    id: root

    property var model

    Row {
        anchors.fill: parent

        ToolButton {
            contentItem: AwesomeIcon {
                name: "refresh"
                size: 12
            }

            visible: repeater.count == 0

            height: parent.height
            width: parent.height
            onClicked: controller.pop()
        }

        Repeater {
            id: repeater
            model: root.model
            delegate: ToolButton {
                id: control

                background: Item { }  // Hide background

                contentItem: Text {
                    text: modelData
                    font: control.font
                    color: control.down ? "#aaa" : "#fff"
                    verticalAlignment: Text.AlignVCenter
                    elide: Text.ElideRight
                }

                height: parent.height
                font.pixelSize: 10
                onClicked: controller.pop()
            }
        }
    }
}