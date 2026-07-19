from __future__ import annotations

from collections.abc import Callable
from typing import Any

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextBrowser,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from engine.ai.provider import AIProvider
from engine.ai.providers import DisabledProvider


class OppenheimerAIPage(QWidget):
    configure_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._context_provider: Callable[[], dict[str, Any]] | None = None
        self._provider: AIProvider = DisabledProvider()

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(10)

        title = QLabel("OPPENHEIMER AI")
        title.setObjectName("pageTitle")
        subtitle = QLabel("KERNEL DEVELOPMENT ASSISTANT · PROVIDER-NEUTRAL FOUNDATION")
        subtitle.setObjectName("pageSubtitle")
        root.addWidget(title)
        root.addWidget(subtitle)

        provider_card = QFrame()
        provider_card.setObjectName("panelCard")
        provider_layout = QHBoxLayout(provider_card)
        self.provider_name = QLabel("AI PROVIDER: NOT CONFIGURED")
        self.provider_description = QLabel(
            "Oppenheimer remains fully usable. Configure OpenAI, Ollama, "
            "or LM Studio later to enable AI responses."
        )
        self.provider_description.setWordWrap(True)
        text_layout = QVBoxLayout()
        text_layout.addWidget(self.provider_name)
        text_layout.addWidget(self.provider_description)
        self.configure_button = QPushButton("CONFIGURE AI")
        self.configure_button.clicked.connect(self.configure_requested.emit)
        provider_layout.addLayout(text_layout, 1)
        provider_layout.addWidget(self.configure_button)
        root.addWidget(provider_card)

        context_card = QFrame()
        context_card.setObjectName("panelCard")
        context_layout = QVBoxLayout(context_card)
        context_layout.addWidget(QLabel("CONTEXT INJECTION"))
        grid = QGridLayout()

        self.include_build_log = QCheckBox("Build log")
        self.include_config = QCheckBox("Kernel config")
        self.include_patches = QCheckBox("Enabled patches")
        self.include_workspace = QCheckBox("Workspace")
        self.include_terminal = QCheckBox("Terminal output")

        for box in (
            self.include_build_log,
            self.include_config,
            self.include_patches,
            self.include_workspace,
        ):
            box.setChecked(True)

        grid.addWidget(self.include_build_log, 0, 0)
        grid.addWidget(self.include_config, 0, 1)
        grid.addWidget(self.include_patches, 0, 2)
        grid.addWidget(self.include_workspace, 1, 0)
        grid.addWidget(self.include_terminal, 1, 1)
        context_layout.addLayout(grid)
        root.addWidget(context_card)

        actions = QHBoxLayout()
        self.explain_build = QPushButton("EXPLAIN BUILD FAILURE")
        self.review_config = QPushButton("REVIEW CONFIG")
        self.review_patches = QPushButton("REVIEW PATCHES")
        self.clear_button = QPushButton("CLEAR")
        actions.addWidget(self.explain_build)
        actions.addWidget(self.review_config)
        actions.addWidget(self.review_patches)
        actions.addStretch(1)
        actions.addWidget(self.clear_button)
        root.addLayout(actions)

        self.history = QTextBrowser()
        self.history.setPlaceholderText(
            "AI responses will appear here after a provider is configured."
        )
        root.addWidget(self.history, 1)

        self.prompt = QTextEdit()
        self.prompt.setMaximumHeight(120)
        self.prompt.setPlaceholderText(
            "Ask about the current kernel, config, patches, build log, or workspace..."
        )
        root.addWidget(self.prompt)

        bottom = QHBoxLayout()
        self.status = QLabel("READY · NO PROVIDER")
        self.send_button = QPushButton("ASK OPPENHEIMER AI")
        bottom.addWidget(self.status)
        bottom.addStretch(1)
        bottom.addWidget(self.send_button)
        root.addLayout(bottom)

        self.send_button.clicked.connect(self.send_prompt)
        self.clear_button.clicked.connect(self.history.clear)
        self.explain_build.clicked.connect(
            lambda: self.quick(
                "Analyze the most recent kernel build output and propose safe fixes."
            )
        )
        self.review_config.clicked.connect(
            lambda: self.quick("Review the current kernel configuration.")
        )
        self.review_patches.clicked.connect(
            lambda: self.quick(
                "Review the enabled patches for compatibility and conflicts."
            )
        )

    def set_context_provider(
        self, provider: Callable[[], dict[str, Any]]
    ) -> None:
        self._context_provider = provider

    def set_provider(self, provider: AIProvider) -> None:
        self._provider = provider

    def selected_context(self) -> dict[str, Any]:
        raw = self._context_provider() if self._context_provider else {}
        result = {
            "application": raw.get("application", {}),
            "kernel": raw.get("kernel", {}),
            "build": raw.get("build", {}),
        }
        if self.include_workspace.isChecked():
            result["workspace"] = raw.get("workspace", {})
        if self.include_config.isChecked():
            result["kernel_config"] = raw.get("kernel_config", {})
        if self.include_patches.isChecked():
            result["patches"] = raw.get("patches", {})
        if self.include_build_log.isChecked():
            result["recent_build_log"] = raw.get("recent_build_log", "")
        if self.include_terminal.isChecked():
            result["recent_terminal_output"] = raw.get(
                "recent_terminal_output", ""
            )
        return result

    def quick(self, text: str) -> None:
        self.prompt.setPlainText(text)
        self.send_prompt()

    def send_prompt(self) -> None:
        prompt = self.prompt.toPlainText().strip()
        if not prompt:
            self.history.append("<b>OPPENHEIMER</b><br>Enter a question first.")
            return

        self.prompt.clear()
        self.history.append(f"<b>YOU</b><br>{self.escape(prompt)}")

        if not self._provider.info().configured:
            self.history.append(
                "<b>OPPENHEIMER</b><br>No AI provider is configured. "
                "Nothing was sent and there is no API charge."
            )
            return

        try:
            result = self._provider.ask(prompt, self.selected_context())
            self.history.append(
                f"<b>OPPENHEIMER AI</b><br>{self.escape(result.text)}"
            )
        except Exception as error:
            self.history.append(
                f"<b>REQUEST FAILED</b><br>{self.escape(str(error))}"
            )

    @staticmethod
    def escape(text: str) -> str:
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )
