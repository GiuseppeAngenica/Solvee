import sys
import math
import toml
from pathlib import Path
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget,
                               QHBoxLayout, QPlainTextEdit)
from PySide6.QtGui import (QColor, QFont, QSyntaxHighlighter,
                           QTextCharFormat)
from PySide6.QtCore import Qt, QRegularExpression

# --- DEFAULT CONFIGURATION ---
# Fallback configuration used if 'theme.toml' is missing or corrupted.
DEFAULT_CONFIG = {
    "color": {
        "background_color": "#1E1E1E",
        "text_color":       "#ABB2BF",
        "number_color":     "#D19A66",
        "operator_color":   "#56B6C2",
        "variable_color":   "#C678DD",
        "assignment_color": "#E06C75",
        "result_color":     "#98C379",
    },
    "font": {
        "family":      "CaskaydiaCove Nerd Font",
        "size":        14,
    }
}

def load_config():
    """
    Loads the configuration from 'theme.toml'.
    Returns DEFAULT_CONFIG if the file is missing or invalid.
    """
    config_path = Path("theme.toml")
    if config_path.exists():
        try:
            with open(config_path, "r") as f:
                return toml.load(f)
        except Exception as e:
            print(f"Warning: Could not load theme.toml ({e}). Using default theme.")
    return DEFAULT_CONFIG

# Load configuration at application startup
CONFIG = load_config()

class SolveeHighlighter(QSyntaxHighlighter):
    """
    Handles syntax highlighting for the calculator input editor.
    Applies color rules defined in the loaded configuration.
    """
    def __init__(self, document):
        super().__init__(document)
        self.rules = []
        
        colors = CONFIG.get("color", DEFAULT_CONFIG["color"])

        # 1. Rule for NUMBERS (integers and floats, e.g., 10, 3.14)
        num_fmt = QTextCharFormat()
        num_fmt.setForeground(QColor(colors["number_color"]))
        self.rules.append((QRegularExpression(r"\b\d+(\.\d+)?\b"), num_fmt))

        # 2. Rule for OPERATORS and SYMBOLS (+ - * / % ^ ( ))
        op_fmt = QTextCharFormat()
        op_fmt.setForeground(QColor(colors["operator_color"]))
        self.rules.append((QRegularExpression(r"[\+\-\*\/\%\^\(\)]"), op_fmt))

        # 3. Rule for ASSIGNMENT OPERATOR (==)
        # Note: We use '==' for assignment to distinguish from result output.
        assign_fmt = QTextCharFormat()
        assign_fmt.setForeground(QColor(colors["assignment_color"]))
        assign_fmt.setFontWeight(QFont.Bold)
        self.rules.append((QRegularExpression(r"=="), assign_fmt))

        # 4. Rule for VARIABLE NAMES (identifiers following '==')
        # Uses a lookbehind assertion to identify text immediately after '=='
        var_fmt = QTextCharFormat()
        var_fmt.setForeground(QColor(colors["variable_color"]))
        var_fmt.setFontItalic(True)
        self.rules.append((QRegularExpression(r"(?<===)\s*[a-zA-Z_]\w*"), var_fmt))

    def highlightBlock(self, text):
        """Applies the highlighting rules to the current block of text."""
        for pattern, fmt in self.rules:
            match_iter = pattern.globalMatch(text)
            while match_iter.hasNext():
                match = match_iter.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), fmt)


class SolveeCalculator(QMainWindow):
    """
    Main Application Window.
    Features a dual-pane layout: Input (Editor) on the left and Output (Display) on the right.
    """
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Solvee v1.1")
        self.resize(600, 450)

        # Extract config values for easier access within the class
        c_conf = CONFIG.get("color", DEFAULT_CONFIG["color"])
        f_conf = CONFIG.get("font", DEFAULT_CONFIG["font"])

        # Apply Global Stylesheet
        self.setStyleSheet(f"""
            QMainWindow {{ background-color: {c_conf['background_color']}; }}
            QPlainTextEdit {{
                background-color: {c_conf['background_color']};
                border: none;
                font-family: '{f_conf['family']}';
                font-size: {f_conf['size']}pt;
            }}
        """)

        # Main Layout Setup
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout(central_widget)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)

        # --- INPUT EDITOR (Left Pane) ---
        self.input_editor = QPlainTextEdit()
        self.input_editor.setStyleSheet(f"color: {c_conf['text_color']};")
        self.input_editor.setPlaceholderText("Type here... (e.g. 10 * 5)")
        
        # Attach Syntax Highlighter to the input document
        self.highlighter = SolveeHighlighter(self.input_editor.document())

        # --- OUTPUT DISPLAY (Right Pane) ---
        self.output_display = QPlainTextEdit()
        self.output_display.setReadOnly(True)
        self.output_display.setStyleSheet(f"color: {c_conf['result_color']};")
        self.output_display.setLayoutDirection(Qt.RightToLeft) # Align results to the right
        self.output_display.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Add widgets to layout (60% width for Input, 40% width for Output)
        layout.addWidget(self.input_editor, 60)
        layout.addWidget(self.output_display, 40)

        # --- SIGNALS & SLOTS ---
        # Trigger recalculation whenever the input text changes
        self.input_editor.textChanged.connect(self.calculate)
        
        # Synchronize Vertical Scrolling between both panes
        self.input_editor.verticalScrollBar().valueChanged.connect(
            self.output_display.verticalScrollBar().setValue
        )
        self.output_display.verticalScrollBar().valueChanged.connect(
            self.input_editor.verticalScrollBar().setValue
        )

    def calculate(self):
        """
        Parses the input line by line, maintaining a persistent variable scope
        from top to bottom, and updates the output pane in real-time.
        """
        input_text = self.input_editor.toPlainText()
        lines = input_text.split('\n')
        results = []
        
        # Initialize variable scope with standard math functions.
        # The scope is reset on every keystroke to ensure clean recalculation from the top.
        scope = {k: v for k, v in math.__dict__.items() if not k.startswith("__")}
        
        for line in lines:
            clean_line = line.strip()
            if not clean_line:
                results.append("")
                continue
            
            try:
                # CASE 1: Variable Assignment
                # Syntax: expression == variable_name (e.g., "10 + 5 == x")
                if "==" in clean_line:
                    expr, var_name = clean_line.split("==", 1)
                    expr = expr.strip().replace("^", "**") # Support caret for exponentiation
                    var_name = var_name.strip()
                    
                    if var_name.isidentifier():
                        # Calculate expression and store result in the scope
                        val = eval(expr, {"__builtins__": {}}, scope)
                        scope[var_name] = val
                        results.append(self.format_result(val))
                    else:
                        results.append("Error: Invalid Name")

                # CASE 2: Standard Expression Evaluation
                # Syntax: expression (e.g., "x * 2")
                else:
                    expr = clean_line.replace("^", "**")
                    # 'scope' contains both math functions and user-defined variables
                    res = eval(expr, {"__builtins__": {}}, scope)
                    results.append(self.format_result(res))
                    
            except Exception:
                # Silently suppress errors to avoid UI clutter while the user is still typing.
                # This mimics the behavior of Numi or Soulver.
                results.append("") 

        self.output_display.setPlainText('\n'.join(results))
        
        # Restore scroll position after updating the text to prevent jumping
        self.output_display.verticalScrollBar().setValue(
            self.input_editor.verticalScrollBar().value()
        )

    def format_result(self, val):
        """
        Helper method to format numerical results cleanly.
        Integers appear without decimals; floats are limited to 2 decimal places.
        """
        if isinstance(val, (int, float)):
            return str(int(val)) if val == int(val) else f"{val:.2f}"
        return ""

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SolveeCalculator()
    window.show()
    sys.exit(app.exec())
