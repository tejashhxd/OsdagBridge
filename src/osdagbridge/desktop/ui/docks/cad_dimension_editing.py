from PySide6.QtCore import QObject, QRectF, Qt, Signal
from PySide6.QtWidgets import QLineEdit

from osdagbridge.core.utils.common import (
    KEY_CARRIAGEWAY_WIDTH,
    KEY_SPAN,
    KEY_TS_DECK_THICKNESS,
    KEY_TS_GIRDER_SPACING,
)


class _DimensionLineEdit(QLineEdit):
    finish_requested = Signal()
    cancel_requested = Signal()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.finish_requested.emit()
            event.accept()
            return
        if event.key() == Qt.Key_Escape:
            self.cancel_requested.emit()
            event.accept()
            return
        super().keyPressEvent(event)

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self.finish_requested.emit()


class CadDimensionEditor(QObject):
    parameter_edited = Signal(str, str)

    _PARAMETERS = {
        KEY_CARRIAGEWAY_WIDTH: ("carriageway_width", 1000.0),
        KEY_TS_GIRDER_SPACING: ("girder_spacing", 1000.0),
        KEY_TS_DECK_THICKNESS: ("deck_thickness", 1.0),
        KEY_SPAN: ("span_length", 1000.0),
    }

    def __init__(self, canvas):
        super().__init__(canvas)
        self.canvas = canvas
        self.enabled = False
        self._labels: list[tuple[QRectF, str]] = []
        self._editor: _DimensionLineEdit | None = None
        self._editing_key: str | None = None
        self._original_text = ""
        self.canvas.setFocusPolicy(Qt.NoFocus)

    def set_enabled(self, enabled: bool):
        self.enabled = enabled
        if not enabled:
            self._cancel_edit()
        self.canvas.setFocusPolicy(Qt.ClickFocus if enabled else Qt.NoFocus)

    def clear_labels(self):
        self._labels.clear()

    def register_label(self, key: str | None, rect: QRectF):
        if self.enabled and key in self._PARAMETERS:
            self._labels.append((QRectF(rect), key))

    def mouse_double_click(self, event, params: dict) -> bool:
        if not self.enabled or self._editor is not None:
            return False

        pos = event.position() if hasattr(event, "position") else event.pos()
        for rect, key in reversed(self._labels):
            if rect.contains(pos):
                param_name, unit_scale = self._PARAMETERS[key]
                value = float(params[param_name]) / unit_scale
                self._open_editor(key, rect, value)
                event.accept()
                return True
        return False

    def mouse_press(self, event):
        if self._editor is None:
            return
        pos = event.position() if hasattr(event, "position") else event.pos()
        if not QRectF(self._editor.geometry()).contains(pos):
            self.canvas.setFocus(Qt.MouseFocusReason)

    def _open_editor(self, key: str, rect: QRectF, value: float):
        editor = _DimensionLineEdit(self.canvas)
        self._editor = editor
        self._editing_key = key
        self._original_text = f"{value:.8g}"

        width = min(self.canvas.width(), max(110, int(rect.width()) + 8))
        height = min(self.canvas.height(), max(24, int(rect.height()) + 4))
        x = int(rect.center().x() - width / 2)
        y = int(rect.center().y() - height / 2)
        x = max(0, min(x, self.canvas.width() - width))
        y = max(0, min(y, self.canvas.height() - height))

        editor.setGeometry(x, y, width, height)
        editor.setAlignment(Qt.AlignCenter)
        editor.setStyleSheet(
            "QLineEdit { background: white; border: 1px solid #90AF13; "
            "padding: 2px; color: #111; }"
        )
        editor.setText(self._original_text)
        editor.finish_requested.connect(self._finish_edit)
        editor.cancel_requested.connect(self._cancel_edit)
        editor.show()
        editor.raise_()
        editor.setFocus(Qt.MouseFocusReason)
        editor.selectAll()

    def _finish_edit(self):
        editor = self._editor
        key = self._editing_key
        if editor is None or key is None:
            return

        text = editor.text().strip()
        unchanged = text == self._original_text
        self._close_editor()
        if not unchanged:
            self.parameter_edited.emit(key, text)

    def _cancel_edit(self):
        if self._editor is None:
            return
        self._close_editor()

    def _close_editor(self):
        editor = self._editor
        self._editor = None
        self._editing_key = None
        self._original_text = ""
        if editor is not None:
            editor.deleteLater()
        self.canvas.update()
