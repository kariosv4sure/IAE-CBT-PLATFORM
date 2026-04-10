# check_questions.py
import json
import os
from pathlib import Path

def count_questions(filepath):
    """Count the number of questions in a JSON file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                return len(data)
            else:
                return 0
    except json.JSONDecodeError:
        return -1  # Invalid JSON
    except Exception as e:
        return -2  # Other error

def analyze_directory(directory="."):
    """Analyze all JSON files in the directory."""
    
    # Expected subjects and their required counts
    expected_counts = {
        "english_language.json": 180,
        "mathematics.json": 120,
        "physics.json": 120,
        "chemistry.json": 120,
        "biology.json": 120,
        "geography.json": 120,
        "agricultural_science.json": 120,
        "arabic.json": 50,
        "principles_of_accounts.json": 120,
        "economics.json": 120,
        "government.json": 120,
        "christian_religious_studies.json": 50,
        "commerce.json": 50,
        "art.json": 50,
        "computer_studies.json": 50,
        "french.json": 50,
        "history.json": 50,
        "home_economics.json": 50,
        "igbo.json": 50,
        "yoruba.json": 50,
        "hausa.json": 50,
        "islamic_studies.json": 120,
        "literature_in_english.json": 50,
        "music.json": 50,
        "physical_and_health_education.json": 50
    }
    
    print("=" * 80)
    print("📊 QUESTION BANK ANALYSIS REPORT")
    print("=" * 80)
    print()
    
    # Find all JSON files
    json_files = sorted(Path(directory).glob("*.json"))
    
    completed_120 = []
    completed_50 = []
    incomplete = []
    empty = []
    missing = []
    invalid = []
    
    for filepath in json_files:
        filename = filepath.name
        count = count_questions(filepath)
        
        if count == -1:
            invalid.append((filename, "Invalid JSON format"))
        elif count == -2:
            invalid.append((filename, "Error reading file"))
        elif count == 0:
            empty.append(filename)
        elif filename in expected_counts:
            if count >= expected_counts[filename]:
                if expected_counts[filename] == 120:
                    completed_120.append((filename, count))
                else:
                    completed_50.append((filename, count))
            else:
                incomplete.append((filename, count, expected_counts[filename]))
        else:
            # File not in expected list
            if count >= 120:
                completed_120.append((filename, count))
            elif count >= 50:
                completed_50.append((filename, count))
            else:
                incomplete.append((filename, count, "unknown requirement"))
    
    # Find missing files
    for expected_file in expected_counts:
        if expected_file not in [f.name for f in json_files]:
            missing.append((expected_file, expected_counts[expected_file]))
    
    # Print report
    print("✅ COMPLETED (120 Questions):")
    print("-" * 40)
    if completed_120:
        for filename, count in completed_120:
            print(f"  ✓ {filename:<35} {count} questions")
    else:
        print("  None")
    print(f"  Total: {len(completed_120)} files")
    print()
    
    print("✅ COMPLETED (50 Questions):")
    print("-" * 40)
    if completed_50:
        for filename, count in completed_50:
            print(f"  ✓ {filename:<35} {count} questions")
    else:
        print("  None")
    print(f"  Total: {len(completed_50)} files")
    print()
    
    print("⚠️ INCOMPLETE (Has questions but not enough):")
    print("-" * 40)
    if incomplete:
        for filename, current, required in incomplete:
            print(f"  ⚠ {filename:<35} {current}/{required} questions")
    else:
        print("  None")
    print()
    
    print("🫗 EMPTY FILES (0 questions):")
    print("-" * 40)
    if empty:
        for filename in empty:
            print(f"  🗑️ {filename}")
    else:
        print("  None")
    print()
    
    print("❌ MISSING FILES (Not created):")
    print("-" * 40)
    if missing:
        for filename, required in missing:
            print(f"  ❌ {filename:<35} (needs {required} questions)")
    else:
        print("  None")
    print()
    
    if invalid:
        print("🚫 INVALID FILES (Corrupted JSON):")
        print("-" * 40)
        for filename, error in invalid:
            print(f"  💥 {filename:<35} - {error}")
        print()
    
    # Summary statistics
    print("=" * 80)
    print("📈 SUMMARY STATISTICS")
    print("=" * 80)
    
    total_files = len(completed_120) + len(completed_50) + len(incomplete) + len(empty) + len(invalid)
    total_questions = sum(c for _, c in completed_120) + sum(c for _, c in completed_50) + sum(c for _, c, _ in incomplete)
    
    print(f"  Total JSON files:        {total_files}")
    print(f"  ✅ Fully complete:        {len(completed_120) + len(completed_50)}")
    print(f"  ⚠️ Incomplete:            {len(incomplete)}")
    print(f"  🫗 Empty:                 {len(empty)}")
    print(f"  ❌ Missing:               {len(missing)}")
    print(f"  💥 Invalid:               {len(invalid)}")
    print(f"  📝 Total questions:       {total_questions}")
    print()
    
    # Calculate completion percentage
    total_expected_files = len(expected_counts)
    completed_files = len([f for f in expected_counts if f in [c[0] for c in completed_120] + [c[0] for c in completed_50]])
    completion_rate = (completed_files / total_expected_files) * 100
    
    print(f"  📊 Overall completion:    {completed_files}/{total_expected_files} files ({completion_rate:.1f}%)")
    print()
    
    print("=" * 80)

if __name__ == "__main__":
    # Check if directory argument provided
    import sys
    if len(sys.argv) > 1:
        directory = sys.argv[1]
    else:
        directory = "."
    
    if not os.path.exists(directory):
        print(f"❌ Directory '{directory}' not found!")
        sys.exit(1)
    
    analyze_directory(directory)
