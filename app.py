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

# Offset Reference Table
OFFSETS = {
    'BPRE': 0x39D5E,  # Fire Red (v1.0) - GBA
    'BPEE': 0x6CC94,  # Emerald - GBA
    'IPKE': 0x70080,  # HeartGold (US) - arm9.bin
    'IPGE': 0x70080,  # SoulSilver (US) - arm9.bin
}

def get_game_code(file_path):
    with open(file_path, 'rb') as f:
        # Check GBA (0xAC)
        f.seek(0xAC)
        code = f.read(4).decode('ascii', errors='ignore')
        if code in OFFSETS:
            return code
        
        # Check NDS (0x0C)
        f.seek(0x0C)
        code = f.read(4).decode('ascii', errors='ignore')
        if code in OFFSETS:
            return code
    return None

def patch_gba(file_path, patch_value, offset):
    with open(file_path, 'r+b') as f:
        f.seek(offset)
        f.write(bytes([patch_value]))

def patch_nds(file_path, patch_value, offset):
    rom = ndspy.rom.NintendoDSRom.fromFile(file_path)
    arm9 = bytearray(rom.arm9) # Convert to bytearray to be mutable
    
    # Check if ARM9 is compressed and handle it if necessary
    # ndspy usually handles decompression when accessing arm9 if it's set up correctly,
    # but we might need to ensure we are patching the right place.
    # For HGSS, the offset 0x70080 is in the DECOMPRESSED arm9.
    
    arm9[offset] = patch_value
    rom.arm9 = arm9
    rom.saveToFile(file_path)

def process_rom(file_path, patch_value):
    game_code = get_game_code(file_path)
    if game_code and game_code in OFFSETS:
        offset = OFFSETS[game_code]
        if game_code in ['BPRE', 'BPEE']:
            patch_gba(file_path, patch_value, offset)
            return True, f"Patched GBA {game_code}"
        elif game_code in ['IPKE', 'IPGE']:
            patch_nds(file_path, patch_value, offset)
            return True, f"Patched NDS {game_code}"
    return False, f"Unsupported or unknown game. Code: {game_code}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/patch', methods=['POST'])
def patch():
    if 'rom' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['rom']
    patch_value = int(request.form.get('threshold', 8))
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    session_id = str(uuid.uuid4())
    session_dir = os.path.join(app.config['UPLOAD_FOLDER'], session_id)
    os.makedirs(session_dir, exist_ok=True)
    
    file_path = os.path.join(session_dir, file.filename)
    file.save(file_path)

    if file.filename.endswith('.zip'):
        # Handle Batch Processing
        extract_dir = os.path.join(session_dir, 'extracted')
        patched_dir = os.path.join(session_dir, 'patched')
        os.makedirs(extract_dir, exist_ok=True)
        os.makedirs(patched_dir, exist_ok=True)
        
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        
        patched_files = []
        for root, dirs, files in os.walk(extract_dir):
            for f in files:
                if f.lower().endswith(('.gba', '.nds')):
                    rom_path = os.path.join(root, f)
                    success, msg = process_rom(rom_path, patch_value)
                    if success:
                        patched_files.append(rom_path)
        
        if not patched_files:
            return jsonify({'error': 'No compatible ROMs found in ZIP'}), 400
        
        zip_out_path = os.path.join(app.config['PATCHED_FOLDER'], f"patched_{session_id}.zip")
        with zipfile.ZipFile(zip_out_path, 'w') as zip_out:
            for pf in patched_files:
                zip_out.write(pf, os.path.relpath(pf, extract_dir))
        
        return jsonify({'download_url': f'/download/{os.path.basename(zip_out_path)}'})

    else:
        # Handle Single File
        success, msg = process_rom(file_path, patch_value)
        if success:
            out_filename = f"patched_{file.filename}"
            out_path = os.path.join(app.config['PATCHED_FOLDER'], out_filename)
            shutil.copy(file_path, out_path)
            return jsonify({'download_url': f'/download/{out_filename}'})
        else:
            return jsonify({'error': msg}), 400

@app.route('/download/<filename>')
def download(filename):
    return send_file(os.path.join(app.config['PATCHED_FOLDER'], filename), as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
