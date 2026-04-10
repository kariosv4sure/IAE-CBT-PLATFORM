# fix_json_files.py
import json
import os
from pathlib import Path

def fix_json_file(filepath):
    """Attempt to fix and validate a JSON file."""
    filename = filepath.name
    
    try:
        # Try to read the file
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Try to parse it
        data = json.loads(content)
        print(f"  ✅ {filename} is actually valid! ({len(data)} questions)")
        return True
        
    except json.JSONDecodeError as e:
        print(f"  🔧 {filename} needs fixing: {e}")
        
        # Try common fixes
        try:
            # Fix 1: Remove trailing commas
            import re
            fixed = re.sub(r',\s*([\]}])', r'\1', content)
            
            # Fix 2: Ensure proper quotes
            # Fix 3: Check for missing brackets
            
            data = json.loads(fixed)
            
            # Save the fixed version
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"  ✅ Fixed and saved {filename} ({len(data)} questions)")
            return True
            
        except Exception as fix_error:
            print(f"  ❌ Could not fix {filename}: {fix_error}")
            return False

def main():
    directory = Path(".")
    json_files = sorted(directory.glob("*.json"))
    
    invalid_files = [
        "agricultural_science.json",
        "arabic.json", 
        "art.json",
        "home_economics.json",
        "igbo.json",
        "literature_in_english.json",
        "music.json",
        "physical_and_health_education.json"
    ]
    
    print("=" * 80)
    print("🔧 JSON FILE REPAIR TOOL")
    print("=" * 80)
    print()
    
    for filename in invalid_files:
        filepath = directory / filename
        if filepath.exists():
            fix_json_file(filepath)
        else:
            print(f"  ❌ {filename} not found!")
    
    print()
    print("=" * 80)
    print("✅ Repair attempt complete! Run check_questions.py again.")
    print("=" * 80)

if __name__ == "__main__":
    main()
