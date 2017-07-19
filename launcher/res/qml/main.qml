import QtQuick 2.7
import QtQuick.Controls 2.0
import QtQuick.Layouts 1.3


ApplicationWindow {
    id: window
    title: controller.title

    visible: true
    width: 500
    height: 500
    minimumHeight: 300
    minimumWidth: 300
    color: "#444"

    header: ColumnLayout {
        Rectangle {
            color: "#333"
            height: 50
            Layout.fillWidth: true
            visible: false

            Rectangle {
                width: 30
                height: width
                x: 10

                anchors.verticalCenter: parent.verticalCenter

                color: "steelblue"
            }

            ColumnLayout {
                spacing: 2
                anchors {
                    left: parent.left
                    top: parent.top
                    margins: 7
                    leftMargin: 50
                }

                Label {
                    text: "Launcher"
                    color: "#eee"
                    font.pixelSize: 13
                    font.bold: true
                }

                Label {
                    text: "Specify the context within which to run software."
                    color: "#eee"
                    font.pixelSize: 10
                }
            }

        }

        MyToolBar {
            Layout.fillHeight: true
            Layout.fillWidth: true
            Layout.topMargin: 5
            Layout.leftMargin: 5
            Layout.rightMargin: 5

            inset: true

            RowLayout {
                anchors.fill: parent

                Breadcrumbs {
                    Layout.fillHeight: true
                    Layout.fillWidth: true
                    model: controller.breadcrumbs
                }

                /** Toggle Terminal on/off
                 */
                MyButton {
                    id: terminalButton
                    icon: "terminal"
                    checkable: true
                    implicitHeight: parent.height
                    implicitWidth: parent.height
                    Layout.alignment: Qt.AlignRight

                    onClicked: terminalTextField.focus = true
                }

                /** Toggle Attribute Editor on/off
                 */
                MyButton {
                    id: attributeEditorButton
                    implicitWidth: parent.height
                    implicitHeight: parent.height
                    checkable: true
                    icon: "adjust"
                    Layout.alignment: Qt.AlignRight
                }
            }
        }
    }

    footer: MyToolBar { }

    /** Main Layout
     *  ____________________
     * |          |         |
     * |          |         |
     * |          |         |
     * |__________|_________|
     * |                    |
     * |                    |
     * |____________________|
     *
     */
    Rectangle {
        id: browserContainer
        border.color: "#222"
        color: "#333"
        clip: true

        anchors {
            top: parent.top
            bottom: terminalContainer.top
            right: attributeEditorContainer.left
            left: parent.left
            margins: 5
        }

        Listing {
            id: browserView
            model: controller.model
            anchors.fill: parent
            anchors.margins: 2
            anchors.topMargin: 5
            anchors.leftMargin: 5
        }
    }

    Rectangle {
        id: attributeEditorContainer
        color: "#333"
        visible: width > 0
        border.color: "#222"

        anchors {
            top: parent.top
            bottom: terminalContainer.top
            right: parent.right
            margins: 5
        }

        width: attributeEditorButton.checked ? parent.width / 2 : 0
        Behavior on width { SmoothedAnimation { velocity: 2000 } }

        Attributes {
            clip: true
            anchors.fill: parent
            anchors.margins: 2
            model: controller.environment
        }
    }

    Rectangle {
        id: terminalContainer

        height: terminalButton.checked ? window.height / 2 : 0

        anchors {
            left: parent.left
            right: parent.right
            bottom: parent.bottom
            margins: 5
        }

        Behavior on height { SmoothedAnimation { velocity: 2000 } }

        border.color: "#222"
        color: "#111"

        clip: true
        visible: height > 0

        ColumnLayout {
            anchors.fill: parent

            ListView {
                id: terminalView
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.margins: 3
                ScrollBar.vertical: ScrollBar { }
                ScrollBar.horizontal: ScrollBar { }

                clip: true
                boundsBehavior: Flickable.StopAtBounds

                model: terminal
                delegate: Text {
                    text: line
                    font.family: "consolas"
                    font.pointSize: 9
                    color: "#eee"
                    wrapMode: Text.WordWrap
                    width: ListView.view.width
                }
            }

            TextField {
                id: terminalTextField
                Layout.fillWidth: true
                background: Item {}
                selectionColor: "#555"
                height: contentHeight + 2
                color: "white"
                cursorVisible: true
                font.family: "consolas"
                font.pointSize: 9

                onAccepted: {
                    controller.command(text)
                    clear()
                }
            }
        }

    }

    /** Respond to changes from controller
     *
     *           ____
     *  ______  /    v  ______
     * |      |        |      |
     * |      |        |      |
     * |______|        |______|
     *          ^____/
     *
     */
    Connections {
        target: controller

        onPushed: browserAnimation.restart()
        onPopped: browserAnimation.restart()
    }

    Connections {
        target: terminal
        onRowsInserted: terminalView.positionViewAtEnd()
    }

    SequentialAnimation {
        id: browserAnimation
        NumberAnimation { target: browserView; property: "opacity"; to: 0; duration: 0 }
        NumberAnimation { target: browserView; property: "opacity"; to: 1; duration: 100 }
    }
}
