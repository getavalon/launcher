import QtQuick 2.6
import QtQuick.Controls 2.1
import QtQuick.Layouts 1.3

ListView {
    id: listView

    section.property: "group"
    section.delegate: Label {
        text: section
        color: "#888"
        verticalAlignment: Text.AlignBottom
        height: 25
        bottomPadding: 3
    }

    delegate: ItemDelegate {
        id: control
        height: 20

        contentItem: RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 5
            spacing: 2
            Layout.alignment: Qt.AlignLeft

            Image {
                source: Qt.resolvedUrl("/%1".arg(model.icon))
                fillMode: Image.PreserveAspectFit
                Layout.fillHeight: true
                Layout.margins: 2
                Layout.maximumWidth: height
            }

            Text {
                text: model.label
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
        onClicked: controller.push(model.label)
    }
}
