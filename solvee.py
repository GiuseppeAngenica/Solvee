import sys
import math
import toml
import re
from pathlib import Path
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget,
                               QHBoxLayout, QPlainTextEdit)
from PySide6.QtGui import (QColor, QFont, QSyntaxHighlighter,
                           QTextCharFormat)
from PySide6.QtCore import Qt, QRegularExpression

# --- DIPENDENZE ---
try:
    import pint
    ureg = pint.UnitRegistry()
    ureg.formatter.default_format = '.2f'
except ImportError:
    ureg = None

# --- CONFIGURAZIONE ---
DEFAULT_CONFIG = {
    "color": {
        "background_color": "#1E1E1E",
        "text_color":       "#ABB2BF",
        "number_color":     "#D19A66",
        "operator_color":   "#56B6C2",
        "variable_color":   "#C678DD",
        "assignment_color": "#E06C75",
        "result_color":     "#98C379",
        "unit_color":       "#D19A66",
        "keyword_color":    "#C678DD",
        "placeholder_color": "#5C6370" # Colore grigio scuro per il placeholder
    },
    "font": {
        "family":      "CaskaydiaCove Nerd Font",
        "size":        14,
    }
}

def load_config():
    paths = [Path("theme.toml"), Path("/usr/share/solvee/theme.toml"), Path.home() / ".config/solvee/theme.toml"]
    for p in paths:
        if p.exists():
            try:
                with open(p, "r") as f: return toml.load(f)
            except: continue
    return DEFAULT_CONFIG

CONFIG = load_config()

class SolveeHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.rules = []
        c = CONFIG.get("color", DEFAULT_CONFIG["color"])

        def add_rule(pattern, color, bold=False, italic=False):
            fmt = QTextCharFormat()
            fmt.setForeground(QColor(color))
            if bold: fmt.setFontWeight(QFont.Bold)
            if italic: fmt.setFontItalic(True)
            self.rules.append((QRegularExpression(pattern), fmt))

        add_rule(r"\b\d+(\.\d+)?\b", c["number_color"])
        add_rule(r"[\+\-\*\/\%\^\(\)]", c["operator_color"])
        add_rule(r"==", c["assignment_color"], bold=True)
        add_rule(r"\b(to|in)\b", c["keyword_color"], bold=True)
        # Unità: cattura lettere e il simbolo del grado
        add_rule(r"(?<=\d)\s*[a-zA-Z°]+|[a-zA-Z°]+(?=\s+(to|in))|(?<=(to|in)\s)[a-zA-Z°]+", c["unit_color"], italic=True)
        add_rule(r"(?<===)\s*[a-zA-Z_]\w*", c["variable_color"], italic=True)

    def highlightBlock(self, text):
        for pattern, fmt in self.rules:
            match_iter = pattern.globalMatch(text)
            while match_iter.hasNext():
                m = match_iter.next()
                self.setFormat(m.capturedStart(), m.capturedLength(), fmt)

class SolveeCalculator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Solvee v1.2.5")
        self.resize(700, 500)
        c = CONFIG.get("color", DEFAULT_CONFIG["color"])
        f = CONFIG.get("font", DEFAULT_CONFIG["font"])

        # CSS migliorato per mostrare il placeholder
        self.setStyleSheet(f"""
            QMainWindow {{ background-color: {c['background_color']}; }}
            QPlainTextEdit {{
                background-color: {c['background_color']};
                color: {c['text_color']};
                border: none;
                font-family: '{f['family']}';
                font-size: {f['size']}pt;
            }}
        """)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(20, 20, 20, 20)

        self.input_editor = QPlainTextEdit()
        # SET PLACEHOLDER E COLORE (Tramite CSS specifico se necessario)
        self.input_editor.setPlaceholderText("Esempi:\n100 + 22%\n25 ml to tablespoon\nx == 10\nx * 5")
        
        self.highlighter = SolveeHighlighter(self.input_editor.document())

        self.output_display = QPlainTextEdit()
        self.output_display.setReadOnly(True)
        self.output_display.setStyleSheet(f"color: {c['result_color']};")
        self.output_display.setLayoutDirection(Qt.RightToLeft)

        layout.addWidget(self.input_editor, 65)
        layout.addWidget(self.output_display, 35)

        self.input_editor.textChanged.connect(self.calculate)
        self.input_editor.verticalScrollBar().valueChanged.connect(
            self.output_display.verticalScrollBar().setValue
        )

    def calculate(self):
        lines = self.input_editor.toPlainText().split('\n')
        results = []
        scope = {k: v for k, v in math.__dict__.items() if not k.startswith("__")}
        
        for line in lines:
            clean = line.strip()
            if not clean:
                results.append(""); continue
            try:
                # 1. TENTA CONVERSIONE (Gestione speciale Temperature)
                conv = self.try_conversion(clean, scope)
                if conv:
                    results.append(conv); continue

                # 2. CALCOLO STANDARD
                proc_line = self.handle_percentages(clean)
                if "==" in proc_line:
                    expr, var = proc_line.split("==", 1)
                    val = eval(expr.strip().replace("^", "**"), {"__builtins__": {}}, scope)
                    scope[var.strip()] = val
                    results.append(self.format_result(val))
                else:
                    res = eval(proc_line.replace("^", "**"), {"__builtins__": {}}, scope)
                    results.append(self.format_result(res))
            except:
                results.append("") 

        self.output_display.setPlainText('\n'.join(results))

    def try_conversion(self, text, scope):
        if not ureg: return None
        # Supporto temperature e unità comuni
        t = text.replace("°C", " celsius").replace("°F", " fahrenheit").replace("°", "")
        parts = re.split(r'\s+(?:to|in)\s+', t, flags=re.IGNORECASE)
        if len(parts) < 2: return None
        
        src_txt, target = " ".join(parts[:-1]).strip(), parts[-1].strip()
        try:
            for v_n, v_v in scope.items():
                if isinstance(v_v, (int, float)):
                    src_txt = re.sub(rf'\b{v_n}\b', str(v_v), src_txt)
            
            # Pint parse
            src_qty = ureg.parse_expression(src_txt)
            # Gestione temperatura (Pint vuole unità specifiche per scalari)
            result = src_qty.to(target)
            
            # Pulizia etichetta finale
            label = target.replace("celsius", "°C").replace("fahrenheit", "°F")
            return f"{self.format_result(result.magnitude)} {label}"
        except:
            return None

    def handle_percentages(self, text):
        text = re.sub(r'(\w+)\s*\+\s*(\d+)%', r'\1 * (1 + \2/100)', text)
        text = re.sub(r'(\w+)\s*\-\s*(\d+)%', r'\1 * (1 - \2/100)', text)
        text = re.sub(r'(\d+)%', r'(\1/100)', text)
        return text

    def format_result(self, val):
        if isinstance(val, (int, float)):
            return str(int(val)) if val == int(val) else f"{val:.2f}"
        return str(val)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SolveeCalculator()
    window.show()
    sys.exit(app.exec())
