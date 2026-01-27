# Solvee 🧮

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Beta%20v1.1-orange?style=for-the-badge)

**Solvee** is a beautiful, minimal, and smart calculator for Linux, inspired by the aesthetics and functionality of *Numi* (macOS).

Linux users have been waiting for a Numi port for years. Solvee is the community answer: a customizable, keyboard-centric calculator that blends perfectly with modern workflows (especially tiling window managers like Hyprland/i3).

> **Note:** This project is currently in early development (v1.1).

---

## ✨ Features

* **Clean Interface:** A minimal, dual-pane layout (Input vs. Output).
* **Real-time Calculation:** Results appear instantly as you type.
* **Variable Support:** Store results using the unique `==` syntax and reuse them in subsequent lines.
* **Syntax Highlighting:** Visual distinction between numbers, operators, and variables.
* **Fully Customizable:** Every color and font can be tweaked via a simple `theme.toml` file.
* **Math Power:** Supports standard arithmetic and power operations (`^` or `**`).

## 🚀 Installation

### Prerequisites
You need **Python 3** installed on your system.

### 1. Clone the repository
```bash
git clone https://github.com/GiuseppeAngenica/Solvee.git
cd Solvee
```

### 2. Install dependencies
Solvee is built with **PySide6** (Qt for Python) and **TOML**.
```bash
pip install -r requirements.txt
```
(On Arch Linux, you can also install `python-pyside6` and `python-toml` via pacman).

### 3. Run Solvee
```bash
python solvee.py
```
## 💡 Usage
Solvee works like a smart notepad. Just type your math on the left, and see the answers on the right.

### Basic Math
```
2 + 2           // Output: 4
10 * 5          // Output: 50
2^3             // Output: 8
math.sqrt(16)   // Output: 4
```

### Using Variables
You can assign values to variables using `==` (double equals) at the end of a line.
```
# Define a variable
1500 == salary

# Use it in the next lines
salary * 0.2 == taxes
salary - taxes
```
### Result:
* `1500`
* `300`
* `1200`

## 🎨 Customization
Solvee looks for a `theme.toml` file in its root directory. You can change the font (e.g., Fira Code, JetBrains Mono, CaskaydiaCove) and the color palette.

### Example `theme.toml`:
```toml
[color]
background_color = "#1E1E1E"
text_color       = "#ABB2BF"
number_color     = "#D19A66"
variable_color   = "#C678DD"
result_color     = "#98C379"

[font]
family = "Monospace"
size = 14
```

## 🗺️ Roadmap

* [x] Basic Arithmetic & Real-time evaluation
* [x] Variable assignments (==)
* [x] Syntax Highlighting
* [x] Theme Configuration via TOML
* [ ] Percentage calculations (e.g., 100 + 20%)
* [ ] Unit Conversions (Currency, Length, etc.)
* [ ] Smart text ignoring (Natural Language Processing)

## 🤝 Contributing

Contributions are welcome! If you want to add features (like unit conversion) or fix bugs, feel free to fork the repo and submit a Pull Request.

## 📄 License

MIT License — free to use and modify.
