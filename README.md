# ⚔️ Shiny % Patcher

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)
![Flask](https://img.shields.io/badge/framework-Flask-lightgrey.svg)

A sophisticated, web-based ROM patching utility designed to modify shiny encounter probabilities in Generation 3 (GBA) and Generation 4 (NDS) Pokémon games. Featuring a nostalgic **HGSS Pokedex-inspired interface** with modern glassmorphism.

---

## ✨ Features

*   **Retro Aesthetics:** Beautiful UI inspired by the HeartGold/SoulSilver Pokedex, utilizing glassmorphism and pixel-perfect details.
*   **Intelligent Patching:** Automatically identifies ROM types (GBA vs NDS) and applies the correct hexadecimal offset.
*   **Batch Processing:** Upload a `.zip` archive containing multiple ROMs; the tool will process them all and return a single patched archive.
*   **Live Probability Calculator:** Real-time conversion between "Human Readable Odds" (e.g., 1/256) and the internal Hexadecimal threshold.
*   **Safe Handling:** Uses temporary session-based processing to ensure your original files aren't overwritten locally.

---

## 📸 Interface Preview

*(Place a screenshot here of the glassmorphic Pokedex UI)*

---

## 🧬 Supported Games

| Game | Platform | Region | Supported |
| :--- | :--- | :--- | :---: |
| **Fire Red (v1.0)** | GBA | US/EU | ✅ |
| **Emerald** | GBA | US/EU | ✅ |
| **HeartGold** | NDS | US | ✅ |
| **SoulSilver** | NDS | US | ✅ |

---

## 🛠️ Technical Breakdown

In the original Pokémon engine, a "Shiny" encounter is determined by a XOR calculation of the Trainer ID, Secret ID, and the Pokémon's Personality Value (PID). If the result is less than a specific **Threshold**, the Pokémon is shiny.

*   **Standard Odds:** Threshold = `8` (8/65536 ≈ 1/8192)
*   **Max Odds (Single Byte):** Threshold = `255` (255/65536 ≈ 1/257)

This tool patches the `CMP` (Compare) instruction in the game's assembly to use your custom threshold.

---

## 🚀 Installation & Setup

### Prerequisites
*   Python 3.10 or higher
*   `pip` (Python package manager)

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/shiny-patcher.git
cd shiny-patcher
```

### 2. Set Up Virtual Environment
```bash
python3 -m venv venv
# On Linux/macOS:
source venv/bin/activate
# On Windows:
.\venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Launch the App
```bash
python app.py
```
Visit `http://localhost:5000` in your browser.

---

## ⚖️ Legal & Disclaimer

**This tool is for educational and archival purposes only.** 
The developers do not condone or encourage the distribution of copyrighted ROM files. Users should only patch ROMs they legally own. This tool does not contain any copyrighted material or Nintendo-proprietary code.

---

## 📜 License
Distributed under the MIT License. See `LICENSE` for more information.
