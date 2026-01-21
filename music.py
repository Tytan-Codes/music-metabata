#!/usr/bin/env python3
"""
Classical Music Metadata Tagger using OpenRouter API
Analyzes FLAC filenames and generates proper classical music metadata
Automatically converts non-FLAC audio files (MP4/M4A/etc) to FLAC using ffmpeg

Requirements:
    pip install mutagen openai
    brew install ffmpeg  (for automatic conversion)

Usage:
    export OPENROUTER_API_KEY="your-api-key-here"
    python3 tag_classical_music.py /path/to/your/music/folder
"""

import os
import sys
import json
import re
import subprocess
import shutil
from pathlib import Path
from mutagen.flac import FLAC
from openai import OpenAI

# Default model - can be changed to any OpenRouter supported model
DEFAULT_MODEL = "google/gemini-3-flash-preview"

def setup_openrouter():
    """Initialize OpenRouter API client"""
    api_key = os.environ.get('OPENROUTER_API_KEY')
    if not api_key:
        print("Error: OPENROUTER_API_KEY environment variable not set")
        print("Get your API key from: https://openrouter.ai/keys")
        sys.exit(1)
    
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )
    return client

def get_metadata_from_openrouter(client, filename, context_files=None):
    """Use OpenRouter to parse filename and generate metadata"""
    
    context = ""
    if context_files:
        context = f"\n\nOther files in the same folder: {', '.join(context_files[:10])}"
    
    prompt = f"""Analyze this classical music filename and extract metadata as JSON.

Filename: {filename}

Return ONLY valid JSON with these fields (use null if uncertain):
{{
    "composer": "Last name, First name",
    "work": "Full work title including catalog number",
    "movement": "Movement number and name if applicable",
    "performers": ["Conductor/Performer names"],
    "orchestra": "Orchestra/Ensemble name",
    "soloists": ["Soloist names"],
    "date": "Recording year if present",
    "disc": "Disc number if multi-disc",
    "track": "Track number"
}}

Guidelines for classical music:
- Composer should be "Last, First" format
- Include catalog numbers (Op., K., BWV, etc.) in work title
- Separate movement info if it's part of a larger work
- Identify conductors, orchestras, and soloists

{context}"""

    try:
        response = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[
                {"role": "user", "content": prompt}
            ],
        )
        text = response.choices[0].message.content.strip()
        
        # Extract JSON from response (handle markdown code blocks)
        json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        if json_match:
            text = json_match.group(1)
        elif text.startswith('```') and text.endswith('```'):
            text = text.strip('`').strip()
            if text.startswith('json'):
                text = text[4:].strip()
        
        metadata = json.loads(text)
        return metadata
    except Exception as e:
        print(f"Error parsing with OpenRouter: {e}")
        return None

def validate_flac_file(file_path):
    """Check if file is a valid FLAC file"""
    try:
        # Check file header for FLAC signature
        with open(file_path, 'rb') as f:
            header = f.read(4)
            if header != b'fLaC':
                return False, f"Not a FLAC file (header: {header[:20]})"
        
        # Try to open with mutagen
        audio = FLAC(file_path)
        return True, audio
    except Exception as e:
        return False, str(e)

def has_proper_metadata(audio):
    """Check if FLAC file has proper classical music metadata"""
    # Essential fields for classical music
    required_fields = {
        'composer': ['COMPOSER'],
        'work': ['ALBUM', 'WORK'],
        'title': ['TITLE'],
        'artist': ['ARTIST', 'ALBUMARTIST'],
    }
    
    missing = []
    for field_name, tag_options in required_fields.items():
        # Check if any of the tag options has a non-empty value
        has_value = False
        for tag in tag_options:
            if tag in audio and audio[tag] and audio[tag][0].strip():
                has_value = True
                break
        if not has_value:
            missing.append(field_name)
    
    if missing:
        return False, missing
    return True, []

def detect_actual_format(file_path):
    """Detect the actual audio format based on file header"""
    try:
        with open(file_path, 'rb') as f:
            header = f.read(12)
            
            # Check for various audio format signatures
            if header[:4] == b'fLaC':
                return 'flac'
            elif header[:4] == b'RIFF' and header[8:12] == b'WAVE':
                return 'wav'
            elif header[:3] == b'ID3' or header[:2] == b'\xff\xfb':
                return 'mp3'
            elif header[:4] == b'OggS':
                return 'ogg'
            elif header[4:8] == b'ftyp' or header[:4] == b'\x00\x00\x00\x18' or header[:4] == b'\x00\x00\x00\x1c' or header[:4] == b'\x00\x00\x00 ':
                # MP4/M4A container (ftyp box or size header)
                return 'm4a'
            else:
                return 'unknown'
    except Exception:
        return 'unknown'

def convert_to_flac(file_path):
    """Convert non-FLAC audio file to FLAC using ffmpeg"""
    file_path = Path(file_path)
    
    # Check if ffmpeg is available
    if not shutil.which('ffmpeg'):
        print("  ⚠ ffmpeg not found. Install with: brew install ffmpeg")
        return None
    
    # Detect actual format for better messaging
    actual_format = detect_actual_format(file_path)
    print(f"  ℹ Detected actual format: {actual_format.upper()}")
    
    # Create temporary output file with a clearly different name
    temp_output = file_path.parent / f".{file_path.stem}_converted.flac"
    
    # Create backup folder on Desktop
    backup_folder = Path.home() / "Desktop" / "music_backups"
    backup_folder.mkdir(parents=True, exist_ok=True)
    
    try:
        print(f"  🔄 Converting {actual_format.upper()} to FLAC using ffmpeg...")
        
        # Run ffmpeg to convert to FLAC
        # Use -loglevel error to reduce output noise
        result = subprocess.run([
            'ffmpeg', '-y', 
            '-loglevel', 'error',
            '-i', str(file_path),
            '-c:a', 'flac',
            '-compression_level', '8',
            str(temp_output)
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            error_msg = result.stderr.strip() if result.stderr else "Unknown error"
            print(f"  ✗ ffmpeg conversion failed: {error_msg[:300]}")
            if temp_output.exists():
                temp_output.unlink()
            return None
        
        # Verify the temp output was created and is valid
        if not temp_output.exists():
            print(f"  ✗ ffmpeg did not produce output file")
            return None
        
        # Backup original file to Desktop folder
        # Use a more descriptive backup name with original format
        backup_name = f"{file_path.stem}_original_{actual_format}{file_path.suffix}"
        backup_path = backup_folder / backup_name
        # If file with same name exists, add a number
        counter = 1
        while backup_path.exists():
            backup_path = backup_folder / f"{file_path.stem}_original_{actual_format}_{counter}{file_path.suffix}"
            counter += 1
        shutil.move(str(file_path), str(backup_path))
        
        # Replace with converted file
        shutil.move(str(temp_output), str(file_path))
        
        print(f"  ✓ Converted successfully (original saved to ~/Desktop/music_backups/)")
        
        # Validate the new file
        is_valid, audio = validate_flac_file(file_path)
        if is_valid:
            return audio
        else:
            print(f"  ✗ Converted file still not valid: {audio}")
            return None
            
    except Exception as e:
        print(f"  ✗ Conversion error: {e}")
        if temp_output.exists():
            temp_output.unlink()
        return None

def apply_metadata_to_flac(file_path, metadata, audio=None):
    """Apply metadata to FLAC file"""
    try:
        # Use provided audio object or validate the file
        if audio is None:
            is_valid, result = validate_flac_file(file_path)
            if not is_valid:
                print(f"  ⚠ Invalid FLAC file: {result}")
                return False
            audio = result
        
        # Clear existing tags
        audio.clear()
        
        # Map metadata to FLAC tags
        if metadata.get('composer'):
            audio['COMPOSER'] = metadata['composer']
        
        if metadata.get('work'):
            audio['ALBUM'] = metadata['work']
            audio['WORK'] = metadata['work']
        
        if metadata.get('movement'):
            audio['TITLE'] = metadata['movement']
        elif metadata.get('work'):
            audio['TITLE'] = metadata['work']
        
        if metadata.get('performers'):
            audio['ARTIST'] = ', '.join(metadata['performers'])
            audio['ALBUMARTIST'] = ', '.join(metadata['performers'])
        
        if metadata.get('orchestra'):
            audio['ORCHESTRA'] = metadata['orchestra']
            audio['ENSEMBLE'] = metadata['orchestra']
        
        if metadata.get('soloists'):
            audio['PERFORMER'] = metadata['soloists']
        
        if metadata.get('date'):
            audio['DATE'] = str(metadata['date'])
        
        if metadata.get('disc'):
            audio['DISCNUMBER'] = str(metadata['disc'])
        
        if metadata.get('track'):
            audio['TRACKNUMBER'] = str(metadata['track'])
        
        audio.save()
        return True
    except Exception as e:
        print(f"  ✗ Error writing metadata: {e}")
        return False

def process_folder(folder_path, client, dry_run=False):
    """Process all FLAC files in folder"""
    folder = Path(folder_path)
    
    if not folder.exists():
        print(f"Error: Folder {folder_path} does not exist")
        return
    
    # Get all FLAC files
    flac_files = list(folder.rglob('*.flac')) + list(folder.rglob('*.FLAC'))
    
    if not flac_files:
        print(f"No FLAC files found in {folder_path}")
        return
    
    print(f"Found {len(flac_files)} FLAC files")
    print(f"Mode: {'DRY RUN (no files will be modified)' if dry_run else 'LIVE (files will be modified)'}")
    print("-" * 60)
    
    for i, file_path in enumerate(flac_files, 1):
        filename = file_path.name
        parent_folder = file_path.parent.name
        
        print(f"\n[{i}/{len(flac_files)}] Processing: {filename}")
        
        # Validate FLAC file before making API call
        is_valid, result = validate_flac_file(file_path)
        if not is_valid:
            print(f"  ⚠ {result}")
            # Attempt to convert to FLAC
            audio = convert_to_flac(file_path)
            if audio is None:
                print(f"  ⏭ Skipping file")
                continue
            result = audio  # Use the converted audio object
        
        # Check if file already has proper metadata
        has_metadata, missing_fields = has_proper_metadata(result)
        if has_metadata:
            print(f"  ✓ Already has proper metadata, skipping")
            continue
        else:
            print(f"  ℹ Missing metadata: {', '.join(missing_fields)}")
        
        # Get context from other files in same folder
        context_files = [f.name for f in file_path.parent.glob('*.flac')]
        
        # Get metadata from OpenRouter
        metadata = get_metadata_from_openrouter(client, filename, context_files)
        
        if metadata:
            print("Generated metadata:")
            for key, value in metadata.items():
                if value:
                    print(f"  {key}: {value}")
            
            if not dry_run:
                success = apply_metadata_to_flac(file_path, metadata, result)
                if success:
                    print("✓ Metadata applied successfully")
                else:
                    print("✗ Failed to apply metadata")
            else:
                print("  (dry run - not applied)")
        else:
            print("✗ Failed to generate metadata")

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 tag_classical_music.py <folder_path> [--dry-run]")
        print("\nOptions:")
        print("  --dry-run    Preview metadata without modifying files")
        print("\nSetup:")
        print("  1. Install dependencies: pip install mutagen openai")
        print("  2. Get API key: https://openrouter.ai/keys")
        print("  3. Set key: export OPENROUTER_API_KEY='your-key-here'")
        sys.exit(1)
    
    folder_path = sys.argv[1]
    dry_run = '--dry-run' in sys.argv
    
    print("Classical Music Metadata Tagger")
    print("=" * 60)
    
    client = setup_openrouter()
    process_folder(folder_path, client, dry_run)
    
    print("\n" + "=" * 60)
    print("Processing complete!")

if __name__ == "__main__":
    main()
