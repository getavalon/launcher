import QtQuick 2.6
import QtQuick.Controls 2.0
import QtQuick.Layouts 1.3

ListView {
    id: listView

    section.property: "group"
    section.delegate: Label {
        text: section
        color: "#888"
        lineHeight: 1.5
        verticalAlignment: Text.AlignVCenter
    }

    delegate: ItemDelegate {
        id: control
        height: 20

        contentItem: RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 5
            spacing: 6
            Layout.alignment: Qt.AlignLeft

            AwesomeIcon {
                name: model.icon
                width: height
            }

            Text {
                text: model.label || model.name
                color: "#eee"
                font: control.font
                Layout.fillHeight: true
                Layout.fillWidth: true
                Layout.margins: 0
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignLeft
            }
        }

        background: Rectangle {
            opacity: control.down ? 0.3 : 0.0
            color: "white"
        }

        width: listView.width - listView.leftMargin - listView.rightMargin
        onClicked: controller.push(listView.model.index(index, null))
    }
}
