# ⚔️ Shiny % Patcher

A web-based tool to modify the internal shiny probability constants for Gen 3 (GBA) and Gen 4 (NDS) Pokémon ROMs. This tool adjusts the threshold value used in the shiny calculation formula.

---

## 🚀 The Stack
* **Backend:** Python 3.10+ / Flask
* **Binary Handling:** `struct` & `mmap`
* **NDS Processing:** `ndspy` (for ARM9 extraction/repacking)
* **Frontend:** HTML5 / Tailwind CSS

---

## 🧬 How it Works
In the original games, a Pokémon is shiny if:
$$(\text{TrainerID} \oplus \text{SecretID}) \oplus (\text{PID}_{high} \oplus \text{PID}_{low}) < \text{Threshold}$$

By increasing the **Threshold** value, we widen the "net" for what constitutes a shiny. 

### 🧮 Shiny Rate Calculator
To find your new threshold for the patcher:
* **Calculation:** Threshold = 65536 / Desired Odds
* **Example (1/256):** 65536 / 256 = 256 (Hex: 0x100)
* **Note:** Standard GBA/NDS checks are 8-bit or 16-bit comparisons. Most simple byte patches (0-255) allow for maximum odds of ~1 in 257.

---

## 📍 Offset Reference Table

| Game | Platform | Target File | Hex Offset | Default Value |
| :--- | :--- | :--- | :--- | :--- |
| **Fire Red (v1.0)** | GBA | rom.gba | 0x39D5E | 0x08 |
| **Emerald** | GBA | rom.gba | 0x6CC94 | 0x08 |
| **HG/SS (US)** | NDS | arm9.bin | 0x70080 | 0x08 |

---

## 🛠️ Installation & Setup

1. Clone the repo:
   git clone https://github.com/adnair2024/shiny-patcher.git
   cd shiny-patcher

2. Install Dependencies:
   pip install flask ndspy

3. Run the Dev Server:
   python app.py

---

## 📦 Features

### 1. Batch Processing
The tool supports uploading a .zip file containing multiple ROMs. The Flask backend will:
1. Unzip the files to a temporary directory.
2. Identify the game type via header reading.
3. Apply the corresponding offset patch to all files.
4. Repackage into a patched_roms.zip for download.

### 2. Live Calculator
The UI includes a slider that converts "Human Readable Odds" (e.g., 1/100) into the raw Hexadecimal value required for the ROM's internal comparison.

---

## 🗺️ Roadmap
- [x] Implement GBA byte-writing logic.
- [x] Integrate ndspy for NDS file structure support.
- [x] Add a Shiny Rate Calculator.
- [x] Batch processing for multiple ROMs.
