APP_STYLE = """
QWidget {
    color: #e9ffff;
    font-size: 14px;
}

QPushButton {
    font-size: 14px;
    font-weight: 600;
}

QCheckBox {
    font-size: 14px;
}

QGroupBox {
    font-size: 14px;
    font-weight: 700;
}

QLabel#title {
    font-size: 22px;
    font-weight: 700;
}

QPlainTextEdit {
    font-size: 14px;
}

QWidget#glassPanel {
    background-color: rgba(4, 10, 13, 215);
    border: 1px solid rgba(0,245,212,125);
    border-radius: 12px;
}

QLabel#appTitle {
    color: #00f5d4;
    font-size: 26px;
    font-weight: 700;
}

QLabel#sectionTitle {
    color: #00f5d4;
    font-size: 14px;
    font-weight: 700;
}

QLabel#statusValue {
    color: #00f5d4;
    font-size: 18px;
    font-weight: 700;
}

QPushButton {
    background-color: rgba(5,28,32,230);
    border: 1px solid #00a996;
    border-radius: 7px;
    padding: 8px;
}

QPushButton:hover {
    background-color: rgba(0,105,95,230);
    border-color: #00f5d4;
}

QPushButton:disabled {
    color: #607171;
    border-color: #304242;
    background-color: rgba(5,10,12,210);
}

QComboBox,
QLineEdit,
QSpinBox {
    background-color: rgba(0,0,0,200);
    border: 1px solid #426966;
    border-radius: 6px;
    padding: 7px;
}

QTextEdit {
    background-color: transparent;
    border: 1px solid rgba(0,245,212,90);
    border-radius: 9px;
    color: #dffefe;
    padding: 8px;
}

QStatusBar {
    background-color: rgba(0,3,5,235);
    color: #cffff8;
    border-top: 1px solid rgba(0,245,212,95);
}

/* ---------------- Installed Kernel Cards ---------------- */

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

QLabel#kernelName {
    color: white;
    font-size: 15px;
    font-weight: bold;
}

QLabel#runningKernelName {
    color: #42ff88;
    font-size: 15px;
    font-weight: bold;
}

QLabel#kernelState {
    color: #b8c8c8;
}

QLabel#runningKernelState {
    color: #42ff88;
    font-weight: bold;
}

QLabel#kernelPath {
    color: #86a6a8;
    font-size: 10px;
}

QLabel#runningBadge {
    background-color: #0d9d39;
    color: white;
    border-radius: 8px;
    padding: 4px 10px;
    font-weight: bold;
}

QPushButton#kernelRemoveButton {
    min-width: 34px;
    max-width: 34px;
    min-height: 34px;
    max-height: 34px;
    padding: 0px;
    font-size: 16px;
}

QPushButton#refreshButton {
    padding-left: 12px;
    padding-right: 12px;
}

QLabel#kernelWarning {
    color: #7ce8d8;
    padding: 6px;
}

QLabel#kernelEmpty {
    color: #7ce8d8;
    font-size: 13px;
}
"""
