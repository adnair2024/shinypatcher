### 🛠️ Shiny % Patcher: Critical Refinement Checklist

- [x] **NDS: ARM9 Encryption & Compression Handling**
    - [x] **Encryption:** `ndspy` handles decryption/decompression during `arm9` property access.
    - [x] **Header Integrity:** `rom.saveToFile()` rebuilds the FAT and headers.
    - [x] **Detailed Logs:** Backend now streams step-by-step logs to the UI.
- [x] **GBA: Signature Scanning (Universal Compatibility)**
    - [x] **Pattern Match:** Implemented scanning for `02 00 00 00 00 40 00 00`.
    - [x] **Version Agnostic:** Successfully handles multiple versions via signature search.

- [x] **Header Verification & Feedback**
    - [x] **Strict Check:** Verifies Game IDs and titles.
    - [x] **User Info:** Detected game info is now part of the log output.

- [x] **Patching Logic: 8-bit vs 16-bit**
    - [x] **Threshold Limits:** Multi-offset support implemented for visual consistency.
    - [x] **HGSS/GBA Coverage:** Added secondary offsets like `0x559A0` (HGSS) and `0x44120` (GBA).

- [x] **Memory & Storage Management**
    - [x] **Session Cleanup:** Implemented background thread for auto-deletion of old files.
    - [x] **Unique Identifiers:** Using `uuid` for session directories.

- [x] **Mathematical Converter**
    - [x] **Formula:** Implemented in `calculate_threshold`.
    - [x] **UI Integration:** Frontend slider values are correctly mapped to backend calculation.
