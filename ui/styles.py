# Oppenheimer Atomic Amber palette
# Primary: #ff9d00
# Highlight: #ffb52e
# Deep amber: #7d5712
# Background: #030b0d
# Green is intentionally retained for "ready/running" status indicators.

APP_STYLE = """
QWidget#appRoot {
    background-color: #030b0d;
}

QWidget {
    color: #f3ead8;
    font-size: 13px;
}

QWidget#pageStack {
    background: transparent;
}

QFrame#sidebar {
    background: transparent;
    border: 1px solid rgba(255, 157, 0, 75);
    border-radius: 12px;
}

QLabel#sidebarBrand {
    color: #ff9d00;
    font-size: 20px;
    font-weight: 800;
}

QLabel#sidebarSubtitle {
    color: #a89472;
    font-size: 10px;
    letter-spacing: 4px;
    padding-left: 30px;
    padding-bottom: 12px;
}

QFrame#modeCard {
    background-color: rgba(255, 157, 0, 12);
    border: 1px solid rgba(255, 157, 0, 80);
    border-radius: 9px;
    margin-bottom: 8px;
}

QLabel#modeTitle, QLabel#modeText,
QLabel#navHeading, QLabel#sectionTitle {
    color: #ff9d00;
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
    color: #ded3c0;
    text-align: left;
    padding: 8px 10px;
    font-weight: 500;
}

QPushButton#navButton:hover {
    background-color: rgba(255, 157, 0, 14);
    color: white;
}

QPushButton#navButton:checked {
    background-color: rgba(126, 70, 0, 90);
    border-color: #e68a00;
    color: white;
}

QLabel#sidebarFooter {
    color: #ff9d00;
    font-size: 16px;
    font-weight: 800;
}

QLabel#pageTitle {
    color: #ff9d00;
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
    background: rgba(24, 15, 7, 120);
    border: 1px solid rgba(255, 157, 0, 55);
    border-bottom: none;
    color: #ded3c0;
    padding: 5px 10px;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background: rgba(255, 157, 0, 18);
    color: white;
}

QLabel#pageSubtitle {
    color: #d0c0a5;
    font-size: 12px;
    letter-spacing: 2px;
    padding-bottom: 4px;
}

QLabel#headerMetric {
    background-color: rgba(15, 10, 5, 220);
    border: 1px solid rgba(255, 157, 0, 70);
    border-radius: 8px;
    color: #ff9d00;
    padding: 10px 14px;
    font-weight: 700;
}

QFrame#glassPanel {
    background: transparent;
    border: 1px solid rgba(255, 157, 0, 90);
    border-radius: 10px;
}

QFrame#miniCard, QFrame#patchCard {
    background-color: rgba(19, 12, 6, 210);
    border: 1px solid rgba(255, 157, 0, 55);
    border-radius: 8px;
}

QLabel#stepNumber {
    color: #ff9d00;
    font-size: 19px;
    font-weight: 800;
}

QLabel#stepName {
    color: white;
    font-weight: 800;
}

QLabel#mutedLabel, QLabel#pathLabel {
    color: #a89472;
    font-size: 11px;
}

QLabel#pathLabel {
    color: #d99a3d;
}

QLabel#patchSummary {
    background-color: rgba(255, 157, 0, 10);
    border: 1px solid rgba(255, 157, 0, 50);
    border-radius: 8px;
    padding: 12px;
    color: #f5e5c4;
}

QLabel#statusValue {
    color: #ff9d00;
    font-size: 20px;
    font-weight: 800;
}

QPushButton {
    background-color: rgba(24, 15, 7, 235);
    border: 1px solid #7d5712;
    border-radius: 7px;
    color: #fff3dc;
    padding: 8px 10px;
    font-weight: 650;
}

QPushButton:hover {
    background-color: rgba(92, 51, 0, 230);
    border-color: #ffb52e;
}

QPushButton#primaryButton {
    background-color: rgba(124, 66, 0, 220);
    border: 1px solid #ff9d00;
    min-height: 22px;
}

QPushButton#primaryButton:hover {
    background-color: rgba(176, 96, 0, 235);
}

QPushButton:disabled {
    color: #6f6658;
    border-color: #4a4032;
    background-color: rgba(12, 8, 4, 220);
}

QComboBox, QLineEdit, QSpinBox, QListWidget {
    background-color: rgba(7, 4, 2, 220);
    border: 1px solid #60451f;
    border-radius: 6px;
    padding: 7px;
    selection-background-color: #8a5000;
}

QCheckBox {
    color: #fff3dc;
    font-weight: 700;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 17px;
    height: 17px;
}

QTextEdit {
    background: transparent;
    border: 1px solid rgba(255, 157, 0, 65);
    border-radius: 8px;
    color: #f5ead4;
    padding: 8px;
}

QStatusBar {
    background-color: rgba(7, 4, 2, 238);
    color: #f5e5c4;
    border-top: 1px solid rgba(255, 157, 0, 95);
}

QLabel#placeholderMessage {
    color: #9f9077;
    font-size: 18px;
}

QFrame#kernelCard {
    background-color: rgba(20,12,6,180);
    border: 1px solid rgba(255,157,0,120);
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

QLabel#kernelState { color: #c9bda8; }
QLabel#kernelPath { color: #9f9077; font-size: 10px; }
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
    background-color: rgba(13, 8, 4, 90);
    border: 1px solid rgba(255, 157, 0, 85);
    border-radius: 10px;
}

QFrame#patchCard:hover {
    background-color: rgba(59, 34, 4, 95);
    border-color: rgba(255, 157, 0, 190);
}

QLabel#patchLibrarySummary {
    color: #e5b663;
    font-size: 11px;
    font-weight: 700;
}

QLabel#patchFeatureList {
    color: #46ff83;
    font-size: 10px;
    font-weight: 600;
}

QCheckBox#patchSubOption {
    color: #46ff83;
    font-size: 10px;
    font-weight: 700;
    spacing: 6px;
}

QCheckBox#patchSubOption::indicator {
    width: 13px;
    height: 13px;
}

QCheckBox#patchSubOption:disabled {
    color: #665b49;
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
    color: #a59a87;
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
