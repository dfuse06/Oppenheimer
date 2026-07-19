APP_STYLE = """
QWidget {
    color: #e8ffff;
    font-size: 13px;
}

QWidget#pageStack {
    background: transparent;
}

QFrame#sidebar {
    background: transparent;
    border: 1px solid rgba(0, 245, 212, 75);
    border-radius: 12px;
}

QLabel#sidebarBrand {
    color: #00f5d4;
    font-size: 20px;
    font-weight: 800;
}

QLabel#sidebarSubtitle {
    color: #86aaa8;
    font-size: 10px;
    letter-spacing: 4px;
    padding-left: 30px;
    padding-bottom: 12px;
}

QFrame#modeCard {
    background-color: rgba(0, 245, 212, 12);
    border: 1px solid rgba(0, 245, 212, 80);
    border-radius: 9px;
    margin-bottom: 8px;
}

QLabel#modeTitle, QLabel#modeText,
QLabel#navHeading, QLabel#sectionTitle {
    color: #00f5d4;
    font-weight: 800;
}

QLabel#modeText {
    font-size: 9px;
}

QLabel#navHeading {
    font-size: 10px;
    padding-top: 10px;
    padding-left: 6px;
}

QPushButton#navButton {
    background: transparent;
    border: 1px solid transparent;
    border-radius: 6px;
    color: #c9dddd;
    text-align: left;
    padding: 8px 10px;
    font-weight: 500;
}

QPushButton#navButton:hover {
    background-color: rgba(0, 245, 212, 14);
    color: white;
}

QPushButton#navButton:checked {
    background-color: rgba(0, 130, 118, 90);
    border-color: #00d8c2;
    color: white;
}

QLabel#sidebarFooter {
    color: #00f5d4;
    font-size: 16px;
    font-weight: 800;
}

QLabel#pageTitle {
    color: #00f5d4;
    font-size: 28px;
    font-weight: 800;
}

QWidget#terminalToolbar,
QTabWidget#terminalTabs,
QTabWidget#terminalTabs::pane {
    background: transparent;
    border: none;
}

QTabBar::tab {
    background: rgba(4, 24, 28, 120);
    border: 1px solid rgba(0, 245, 212, 55);
    border-bottom: none;
    color: #c9dddd;
    padding: 5px 10px;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background: rgba(0, 245, 212, 18);
    color: white;
}

QLabel#pageSubtitle {
    color: #b7d0cf;
    font-size: 12px;
    letter-spacing: 2px;
    padding-bottom: 4px;
}

QLabel#headerMetric {
    background-color: rgba(2, 12, 15, 220);
    border: 1px solid rgba(0, 245, 212, 70);
    border-radius: 8px;
    color: #00f5d4;
    padding: 10px 14px;
    font-weight: 700;
}

QFrame#glassPanel {
    background: transparent;
    border: 1px solid rgba(0, 245, 212, 90);
    border-radius: 10px;
}

QFrame#miniCard, QFrame#patchCard {
    background-color: rgba(2, 17, 20, 210);
    border: 1px solid rgba(0, 245, 212, 55);
    border-radius: 8px;
}

QLabel#stepNumber {
    color: #00f5d4;
    font-size: 19px;
    font-weight: 800;
}

QLabel#stepName {
    color: white;
    font-weight: 800;
}

QLabel#mutedLabel, QLabel#pathLabel {
    color: #89a8a7;
    font-size: 11px;
}

QLabel#pathLabel {
    color: #5fc9bd;
}

QLabel#patchSummary {
    background-color: rgba(0, 245, 212, 10);
    border: 1px solid rgba(0, 245, 212, 50);
    border-radius: 8px;
    padding: 12px;
    color: #cffff9;
}

QLabel#statusValue {
    color: #00f5d4;
    font-size: 20px;
    font-weight: 800;
}

QPushButton {
    background-color: rgba(4, 24, 28, 235);
    border: 1px solid #008f83;
    border-radius: 7px;
    color: #eaffff;
    padding: 8px 10px;
    font-weight: 650;
}

QPushButton:hover {
    background-color: rgba(0, 96, 88, 230);
    border-color: #00f5d4;
}

QPushButton#primaryButton {
    background-color: rgba(0, 115, 104, 210);
    border: 1px solid #00f5d4;
    min-height: 22px;
}

QPushButton#primaryButton:hover {
    background-color: rgba(0, 165, 148, 225);
}

QPushButton:disabled {
    color: #566868;
    border-color: #2e4141;
    background-color: rgba(4, 9, 11, 220);
}

QComboBox, QLineEdit, QSpinBox, QListWidget {
    background-color: rgba(0, 3, 5, 220);
    border: 1px solid #355d5a;
    border-radius: 6px;
    padding: 7px;
    selection-background-color: #007e72;
}

QCheckBox {
    color: #eaffff;
    font-weight: 700;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 17px;
    height: 17px;
}

QTextEdit {
    background: transparent;
    border: 1px solid rgba(0, 245, 212, 65);
    border-radius: 8px;
    color: #dffefe;
    padding: 8px;
}

QStatusBar {
    background-color: rgba(0, 3, 5, 238);
    color: #cffff8;
    border-top: 1px solid rgba(0, 245, 212, 95);
}

QLabel#placeholderMessage {
    color: #7ea7a4;
    font-size: 18px;
}

QFrame#kernelCard {
    background-color: rgba(8,18,22,180);
    border: 1px solid rgba(0,245,212,120);
    border-radius: 10px;
    margin: 4px;
}

QFrame#runningKernelCard {
    background-color: rgba(5,65,28,210);
    border: 2px solid #32ff7a;
    border-radius: 10px;
    margin: 4px;
}

QLabel#kernelName, QLabel#runningKernelName {
    color: white;
    font-size: 15px;
    font-weight: bold;
}

QLabel#runningKernelName, QLabel#runningKernelState {
    color: #42ff88;
}

QLabel#kernelState { color: #b8c8c8; }
QLabel#kernelPath { color: #86a6a8; font-size: 10px; }
QLabel#runningBadge {
    background-color: #0d9d39;
    color: white;
    border-radius: 8px;
    padding: 4px 10px;
    font-weight: bold;
}
QPushButton#kernelRemoveButton {
    min-width: 34px; max-width: 34px;
    min-height: 34px; max-height: 34px;
    padding: 0px;
}

/* Add or replace these PATCH LIBRARY rules in ui/styles.py */

QWidget#patchGridWidget,
QScrollArea#patchScroll,
QScrollArea#patchScroll > QWidget > QWidget {
    background: transparent;
}

QFrame#patchCard {
    background-color: rgba(1, 12, 14, 90);
    border: 1px solid rgba(0, 245, 212, 85);
    border-radius: 10px;
}

QFrame#patchCard:hover {
    background-color: rgba(0, 45, 42, 95);
    border-color: rgba(0, 245, 212, 190);
}

QLabel#patchLibrarySummary {
    color: #8fe9df;
    font-size: 11px;
    font-weight: 700;
}

QLabel#patchFeatureList {
    color: #46ff83;
    font-size: 10px;
    font-weight: 600;
}

QLabel#patchStatus {
    color: #ff5c66;
    font-size: 10px;
    font-weight: 800;
}

QLabel#patchStatus[ready="true"] {
    color: #46ff83;
}

QLabel#patchSelectionState {
    color: #91a9a7;
    font-size: 10px;
    font-weight: 700;
}

QLabel#patchSelectionState[enabled="true"] {
    color: #46ff83;
}

QPushButton#patchValidateButton {
    padding: 5px 10px;
    min-height: 18px;
}
"""
