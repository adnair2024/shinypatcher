import os
import zipfile
import shutil
import uuid
from flask import Flask, render_template, request, send_file, jsonify
import ndspy.rom

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['PATCHED_FOLDER'] = 'static/patched'
app.config['MAX_CONTENT_LENGTH'] = 512 * 1024 * 1024  # 512MB limit

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PATCHED_FOLDER'], exist_ok=True)

# Offset Reference Table (Fallbacks)
OFFSETS = {
    'BPRE': 0x39D5E,  # Fire Red (v1.0) US
    'BPZE': 0x39D5E,  # Fire Red (v1.0) DE
    'BPEE': 0x6CC94,  # Emerald US
    'IPKE': 0x70080,  # HeartGold (US)
    'IPGE': 0x70080,  # SoulSilver (US)
    'IPKJ': 0x70080,  # HeartGold (JP)
    'IPGJ': 0x70080,  # SoulSilver (JP)
    'IPKP': 0x70080,  # HeartGold (EU)
    'IPGP': 0x70080,  # SoulSilver (EU)
}

GBA_SIGNATURE = bytes.fromhex('02 00 00 00 00 40 00 00')

def calculate_threshold(odds):
    """threshold = floor(65536 / desired_odds)"""
    if odds <= 1: return 255 # Max 8-bit for now
    threshold = int(65536 / odds)
    return min(max(threshold, 1), 255)

def find_gba_offset(file_path):
    with open(file_path, 'rb') as f:
        data = f.read()
        index = data.find(GBA_SIGNATURE)
        if index != -1:
            return index + 6
    return None

def get_game_info(file_path):
    with open(file_path, 'rb') as f:
        # Check NDS (0x0C)
        f.seek(0x00)
        title = f.read(12).decode('ascii', errors='ignore').strip()
        f.seek(0x0C)
        code = f.read(4).decode('ascii', errors='ignore')
        
        if code in OFFSETS or code.startswith('I'):
             return {'type': 'NDS', 'code': code, 'title': title}

        # Check GBA (0xAC)
        f.seek(0xA0)
        title_gba = f.read(12).decode('ascii', errors='ignore').strip()
        f.seek(0xAC)
        code_gba = f.read(4).decode('ascii', errors='ignore')
        if code_gba in OFFSETS or code_gba.startswith('B'):
            return {'type': 'GBA', 'code': code_gba, 'title': title_gba}
            
    return None

import time
import threading

# ... existing imports ...

# Extended Offsets for consistency (Pokedex, Summary Screen, etc.)
# Logic: Primary offset is used for the check, others are for visual consistency
GBA_MULTI_OFFSETS = {
    'BPRE': [0x39D5E, 0x44120, 0x444B0, 0xF1770, 0x104A24], # Fire Red 1.0
}

def cleanup_old_sessions():
    while True:
        now = time.time()
        for folder in [app.config['UPLOAD_FOLDER'], app.config['PATCHED_FOLDER']]:
            for item in os.listdir(folder):
                item_path = os.path.join(folder, item)
                if os.path.getmtime(item_path) < now - 3600: # 1 hour old
                    if os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                    else:
                        os.remove(item_path)
        time.sleep(600) # Run every 10 minutes

# Start cleanup thread
threading.Thread(target=cleanup_old_sessions, daemon=True).start()

def patch_gba(file_path, patch_value, logs):
    game_code = "Unknown"
    with open(file_path, 'rb') as f:
        f.seek(0xAC)
        game_code = f.read(4).decode('ascii', errors='ignore')

    primary_offset = find_gba_offset(file_path)
    offsets_to_patch = []

    if primary_offset:
        logs.append(f"[*] Primary signature found at {hex(primary_offset-6)}.")
        offsets_to_patch.append(primary_offset)
    elif game_code in OFFSETS:
        offsets_to_patch.append(OFFSETS[game_code])
        logs.append(f"[!] Primary signature not found. Using fallback {hex(OFFSETS[game_code])}.")

    # Add extra visual offsets if known
    if game_code in GBA_MULTI_OFFSETS:
        # We need to be careful with hardcoded secondary offsets 
        # as they shift more between versions than the main logic.
        # For now, only use them if it's BPRE (Fire Red 1.0)
        for off in GBA_MULTI_OFFSETS[game_code]:
            if off not in offsets_to_patch:
                offsets_to_patch.append(off)

    if not offsets_to_patch:
        logs.append(f"[X] Error: No offsets found for {game_code}")
        return False

    with open(file_path, 'r+b') as f:
        for offset in offsets_to_patch:
            try:
                f.seek(offset)
                old_val = f.read(1)[0]
                f.seek(offset)
                # Note: Some visual checks might need patch_value vs patch_value-1
                # but we'll stick to patch_value for consistency for now.
                f.write(bytes([patch_value]))
                logs.append(f"[+] Patched {hex(offset)}: {hex(old_val)} -> {hex(patch_value)}")
            except:
                logs.append(f"[!] Warning: Failed to patch {hex(offset)}")
    return True

def patch_nds(file_path, patch_value, logs):
    try:
        logs.append("[*] Opening NDS ROM with ndspy...")
        rom = ndspy.rom.NintendoDSRom.fromFile(file_path)
        
        game_code = rom.gameCode.decode('ascii', errors='ignore')
        offset = OFFSETS.get(game_code, 0x70080)
        
        logs.append(f"[*] Accessing ARM9 (Handling encryption/compression)...")
        # ndspy's arm9 property automatically handles decompression/decryption 
        # when accessed if the ROM was loaded correctly.
        arm9 = bytearray(rom.arm9)
        
        if offset >= len(arm9):
            logs.append(f"[X] Error: Offset {hex(offset)} out of bounds for ARM9.")
            return False

        old_val = arm9[offset]
        arm9[offset] = patch_value
        rom.arm9 = arm9
        
        logs.append("[*] Rebuilding ROM...")
        rom.saveToFile(file_path)
        logs.append(f"[+] Success: {hex(old_val)} -> {hex(patch_value)} at {hex(offset)}")
        return True
    except Exception as e:
        logs.append(f"[X] NDS Error: {str(e)}")
        return False

def process_rom(file_path, patch_value):
    logs = []
    info = get_game_info(file_path)
    if not info:
        logs.append(f"[X] Error: Could not identify ROM {os.path.basename(file_path)}")
        return False, logs

    logs.append(f"--- Processing {info['title']} ({info['code']}) ---")
    
    if info['type'] == 'GBA':
        success = patch_gba(file_path, patch_value, logs)
        return success, logs
    elif info['type'] == 'NDS':
        success = patch_nds(file_path, patch_value, logs)
        return success, logs
        
    return False, logs

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/patch', methods=['POST'])
def patch():
    if 'rom' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['rom']
    # Threshold calculation based on human-readable odds
    try:
        odds_val = int(request.form.get('threshold', 8192))
        patch_value = calculate_threshold(odds_val)
    except:
        patch_value = 8
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    session_id = str(uuid.uuid4())
    session_dir = os.path.join(app.config['UPLOAD_FOLDER'], session_id)
    os.makedirs(session_dir, exist_ok=True)
    
    file_path = os.path.join(session_dir, file.filename)
    file.save(file_path)

    all_logs = []
    
    try:
        if file.filename.endswith('.zip'):
            extract_dir = os.path.join(session_dir, 'extracted')
            os.makedirs(extract_dir, exist_ok=True)
            
            all_logs.append(f"[*] Extracting ZIP: {file.filename}")
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            patched_files = []
            for root, dirs, files in os.walk(extract_dir):
                for f in files:
                    if f.lower().endswith(('.gba', '.nds')):
                        rom_path = os.path.join(root, f)
                        success, logs = process_rom(rom_path, patch_value)
                        all_logs.extend(logs)
                        if success:
                            patched_files.append(rom_path)
            
            if not patched_files:
                return jsonify({'error': 'No compatible ROMs found in ZIP', 'logs': all_logs}), 400
            
            zip_out_path = os.path.join(app.config['PATCHED_FOLDER'], f"patched_{session_id}.zip")
            all_logs.append(f"[*] Packaging {len(patched_files)} ROMs into ZIP...")
            with zip_out_file := zipfile.ZipFile(zip_out_path, 'w'):
                for pf in patched_files:
                    zip_out_file.write(pf, os.path.relpath(pf, extract_dir))
            
            all_logs.append("[+] Batch processing complete.")
            return jsonify({
                'download_url': f'/download/{os.path.basename(zip_out_path)}',
                'logs': all_logs
            })

        else:
            info = get_game_info(file_path)
            success, logs = process_rom(file_path, patch_value)
            all_logs.extend(logs)
            if success:
                out_filename = f"patched_{file.filename}"
                out_path = os.path.join(app.config['PATCHED_FOLDER'], out_filename)
                shutil.copy(file_path, out_path)
                all_logs.append(f"[+] Single file patch complete.")
                return jsonify({
                    'download_url': f'/download/{out_filename}',
                    'logs': all_logs,
                    'game_type': info['type'] if info else 'GBA'
                })
            else:
                return jsonify({'error': 'Patching failed', 'logs': all_logs}), 400
    finally:
        # Cleanup could be added here
        pass

@app.route('/download/<filename>')
def download(filename):
    return send_file(os.path.join(app.config['PATCHED_FOLDER'], filename), as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
