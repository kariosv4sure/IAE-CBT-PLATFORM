# import.py
import json
import os
from app import app, db, Question

def clean_answer(answer):
    """Extract just the letter from correct_answer"""
    if not answer:
        return 'A'
    answer = str(answer).strip().upper()
    if answer and answer[0] in ['A', 'B', 'C', 'D']:
        return answer[0]
    if 'A' in answer:
        return 'A'
    if 'B' in answer:
        return 'B'
    if 'C' in answer:
        return 'C'
    if 'D' in answer:
        return 'D'
    return 'A'

def import_json_files(folder_path):
    with app.app_context():
        # Clear existing questions first
        print("🗑️  Clearing existing questions...")
        db.session.query(Question).delete()
        db.session.commit()
        
        print("📥 Importing new questions...")
        count = 0
        failed_files = []
        
        for filename in os.listdir(folder_path):
            if not filename.endswith('.json'):
                continue
            if filename in ['check.py', 'fix.py']:
                continue
                
            filepath = os.path.join(folder_path, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    questions = json.load(f)
                
                for q in questions:
                    raw_answer = q.get('correct_answer', 'A')
                    clean_ans = clean_answer(raw_answer)
                    
                    question = Question(
                        subject=q.get('subject', filename.replace('.json', '').replace('_', ' ').title()),
                        question_text=q.get('question_text', q.get('question', '')),
                        option_a=q.get('option_a', ''),
                        option_b=q.get('option_b', ''),
                        option_c=q.get('option_c', ''),
                        option_d=q.get('option_d', ''),
                        correct_answer=clean_ans,
                        explanation=q.get('explanation', '')
                    )
                    db.session.add(question)
                    count += 1
                
                db.session.commit()
                print(f"✅ Imported {filename}: {len(questions)} questions")
                
            except Exception as e:
                db.session.rollback()
                failed_files.append(f"{filename}: {str(e)}")
                print(f"❌ Failed {filename}: {str(e)}")
        
        print(f"\n{'='*50}")
        print(f"📊 IMPORT SUMMARY")
        print(f"{'='*50}")
        print(f"✅ Total imported: {count} questions")
        if failed_files:
            print(f"❌ Failed files: {len(failed_files)}")
            for f in failed_files:
                print(f"   - {f}")
        print(f"{'='*50}")

if __name__ == '__main__':
    import_questions_path = 'data/questions'
    
    if not os.path.exists(import_questions_path):
        print(f"❌ Folder not found: {import_questions_path}")
        print("Make sure you're in the correct directory and the 'data/questions' folder exists.")
    else:
        print(f"📁 Loading questions from: {import_questions_path}")
        import_json_files(import_questions_path)
