# app.py
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone
import os
import random
import uuid
import requests
from functools import wraps
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'iae_secret_key_change_me')

database_url = os.environ.get('DATABASE_URL')
if database_url:
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    if 'sslmode' not in database_url:
        separator = '&' if '?' in database_url else '?'
        database_url += f'{separator}sslmode=require'
else:
    database_url = 'sqlite:///iae_cbt.db'

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

if 'render.com' in database_url or 'oregon-postgres' in database_url:
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'connect_args': {'sslmode': 'require', 'connect_timeout': 10},
        'pool_size': 5,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
    }

db = SQLAlchemy(app)

GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

FOUNDER_NAME = "Moses Daniel"
FOUNDER_EMAIL = "mosesdanielfiyinfoluwa08@gmail.com"
FOUNDER_PHONE = "07079396111"
FOUNDER_WHATSAPP = "2347079396111"

JAMB_SUBJECTS = [
    'English Language', 'Mathematics', 'Physics', 'Chemistry', 'Biology',
    'Agricultural Science', 'Arabic', 'Christian Religious Studies', 'Commerce',
    'Art', 'Computer Studies', 'Economics', 'French', 'Geography', 'Government',
    'Hausa', 'History', 'Home Economics', 'Igbo', 'Islamic Studies',
    'Literature in English', 'Music', 'Physical and Health Education',
    'Principles of Accounts', 'Yoruba'
]

COMPULSORY_SUBJECT = 'English Language'
COMPULSORY_QUESTIONS = 60
ELECTIVE_QUESTIONS_PER_SUBJECT = 40


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    full_name = db.Column(db.String(150), nullable=False)
    is_vip = db.Column(db.Boolean, default=False)
    has_taken_exam = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    subjects = db.relationship('UserSubject', back_populates='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_chosen_subjects(self):
        return [us.subject_name for us in self.subjects if us.subject_name != COMPULSORY_SUBJECT]


class UserSubject(db.Model):
    __tablename__ = 'user_subjects'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    subject_name = db.Column(db.String(50), nullable=False)
    user = db.relationship('User', back_populates='subjects')
    __table_args__ = (db.UniqueConstraint('user_id', 'subject_name', name='unique_user_subject'),)


class ExamSession(db.Model):
    __tablename__ = 'exam_sessions'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_active_at = db.Column(db.DateTime, default=datetime.utcnow)
    submitted_at = db.Column(db.DateTime, nullable=True)
    cancelled = db.Column(db.Boolean, default=False)
    score = db.Column(db.Integer, nullable=True)
    total_questions = db.Column(db.Integer, default=180)
    active_session_token = db.Column(db.String(100), unique=True, nullable=True)
    user = db.relationship('User', backref=db.backref('exam_sessions', lazy=True))


class Question(db.Model):
    __tablename__ = 'questions'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    subject = db.Column(db.String(50), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.String(500), nullable=False)
    option_b = db.Column(db.String(500), nullable=False)
    option_c = db.Column(db.String(500), nullable=False)
    option_d = db.Column(db.String(500), nullable=False)
    correct_answer = db.Column(db.String(1), nullable=False)
    explanation = db.Column(db.Text, nullable=True)


class UserAnswer(db.Model):
    __tablename__ = 'user_answers'
    session_id = db.Column(db.String(36), db.ForeignKey('exam_sessions.id'), primary_key=True)
    question_id = db.Column(db.String(36), db.ForeignKey('questions.id'), primary_key=True)
    selected_answer = db.Column(db.String(1), nullable=True)
    is_correct = db.Column(db.Boolean, default=False)
    saved_at = db.Column(db.DateTime, default=datetime.utcnow)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            flash('Admin access required.', 'error')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function


def vip_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to continue.', 'warning')
            return redirect(url_for('login'))
        user = db.session.get(User, session['user_id'])
        if not user or not user.is_vip:
            flash('VIP access required for this feature.', 'warning')
            return redirect(url_for('unrestricted'))
        return f(*args, **kwargs)
    return decorated_function


def get_current_user():
    if 'user_id' in session:
        return db.session.get(User, session['user_id'])
    return None


def generate_explanation_with_groq(question_text, options, correct_answer, subject):
    if not GROQ_API_KEY:
        return None

    try:
        prompt = f"""You are a JAMB CBT tutor. Explain this {subject} question clearly and concisely.

Question: {question_text}

Options:
A: {options['A']}
B: {options['B']}
C: {options['C']}
D: {options['D']}

Correct Answer: {correct_answer}

Provide a brief, educational explanation (2-4 sentences) why {correct_answer} is correct."""

        response = requests.post(
            GROQ_API_URL,
            json={
                "model": "mixtral-8x7b-32768",
                "messages": [
                    {"role": "system", "content": "You are a helpful JAMB tutor providing concise explanations."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 150,
                "temperature": 0.3
            },
            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
            timeout=10
        )

        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content'].strip()
        return None
    except Exception:
        return None


def get_questions_for_user(user):
    """Get exactly 180 questions: 60 English + 40 from each of 3 chosen subjects"""
    chosen_subjects = user.get_chosen_subjects()
    if len(chosen_subjects) != 3:
        raise ValueError("User must have exactly 3 chosen subjects.")

    selected_questions = []
    warnings = []

    # Get English questions
    english_qs = Question.query.filter_by(subject=COMPULSORY_SUBJECT).all()
    if len(english_qs) >= COMPULSORY_QUESTIONS:
        selected_questions.extend(random.sample(english_qs, COMPULSORY_QUESTIONS))
    else:
        selected_questions.extend(english_qs)
        warnings.append(f"{COMPULSORY_SUBJECT} (only {len(english_qs)}/{COMPULSORY_QUESTIONS} questions)")

    # Get elective subject questions
    for subj in chosen_subjects:
        subj_qs = Question.query.filter_by(subject=subj).all()
        if len(subj_qs) >= ELECTIVE_QUESTIONS_PER_SUBJECT:
            selected_questions.extend(random.sample(subj_qs, ELECTIVE_QUESTIONS_PER_SUBJECT))
        else:
            selected_questions.extend(subj_qs)
            warnings.append(f"{subj} (only {len(subj_qs)}/{ELECTIVE_QUESTIONS_PER_SUBJECT} questions)")

    # Store warnings in session to show user
    if warnings:
        flash(f'Warning: Limited questions available for: {", ".join(warnings)}', 'warning')

    random.shuffle(selected_questions)
    return selected_questions[:180]  # Ensure exactly 180


@app.route('/')
def index():
    return render_template('index.html', user=get_current_user())


@app.route('/about')
def about():
    return render_template('about.html', user=get_current_user())


@app.route('/privacy')
def privacy():
    return render_template('privacy.html', user=get_current_user())


@app.route('/terms')
def terms():
    return render_template('terms.html', user=get_current_user())


@app.route('/contact')
def contact():
    return render_template('contact.html', user=get_current_user())


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            username = request.form['username'].strip()
            email = request.form['email'].strip()
            password = request.form['password']
            full_name = request.form['full_name'].strip()
            subjects = [
                request.form.get('subject1'),
                request.form.get('subject2'),
                request.form.get('subject3')
            ]

            error = None
            if User.query.filter_by(username=username).first():
                error = 'Username already taken.'
            elif User.query.filter_by(email=email).first():
                error = 'Email already registered.'
            elif len(password) < 6:
                error = 'Password must be at least 6 characters.'
            elif not all(subjects) or len(set(subjects)) != 3:
                error = 'Please select exactly 3 distinct subjects.'
            elif any(s == COMPULSORY_SUBJECT for s in subjects):
                error = f'{COMPULSORY_SUBJECT} is compulsory and automatically included.'

            if error:
                flash(error, 'error')
                return render_template('register.html', form_data=request.form, subjects_list=JAMB_SUBJECTS, user=None)

            user = User(username=username, email=email, full_name=full_name)
            user.set_password(password)
            db.session.add(user)
            db.session.flush()

            for subj in subjects:
                db.session.add(UserSubject(user_id=user.id, subject_name=subj))

            db.session.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during registration. Please try again.', 'error')
            return render_template('register.html', form_data=request.form, subjects_list=JAMB_SUBJECTS, user=None)

    return render_template('register.html', user=None, subjects_list=JAMB_SUBJECTS)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            flash(f'Welcome back, {user.full_name}!', 'success')
            return redirect(url_for('dashboard') if user.is_vip else url_for('unrestricted'))

        flash('Invalid username or password.', 'error')

    return render_template('login.html', user=None)


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


@app.route('/unrestricted')
@login_required
def unrestricted():
    return render_template('unrestricted.html', user=get_current_user())


@app.route('/dashboard')
@login_required
@vip_required
def dashboard():
    user = get_current_user()
    active_session = ExamSession.query.filter_by(user_id=user.id, submitted_at=None, cancelled=False).first()
    return render_template('dashboard.html', user=user, active_session=active_session)


@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=get_current_user())


@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html', user=get_current_user())


@app.route('/exam/start')
@login_required
@vip_required
def start_exam():
    user = get_current_user()

    if user.has_taken_exam:
        flash('You have already completed the exam.', 'info')
        return redirect(url_for('result'))

    existing = ExamSession.query.filter_by(user_id=user.id, submitted_at=None, cancelled=False).first()
    if existing:
        return redirect(url_for('resume_exam'))

    try:
        questions = get_questions_for_user(user)
    except ValueError as e:
        flash(str(e), 'error')
        return redirect(url_for('dashboard'))

    if not questions:
        flash('No questions available for your subjects. Please contact admin.', 'error')
        return redirect(url_for('dashboard'))

    exam_session = ExamSession(
        user_id=user.id,
        active_session_token=str(uuid.uuid4()),
        total_questions=len(questions)
    )
    db.session.add(exam_session)
    db.session.commit()

    session['exam_questions'] = [q.id for q in questions]
    session['exam_session_id'] = exam_session.id
    session['exam_start_time'] = datetime.now(timezone.utc).isoformat()

    # ✅ Convert questions to dicts for JSON serialization
    questions_data = [{
        'id': q.id,
        'question_text': q.question_text,
        'option_a': q.option_a,
        'option_b': q.option_b,
        'option_c': q.option_c,
        'option_d': q.option_d
    } for q in questions]

    return render_template('exam.html', user=user, questions=questions_data,
                           session_id=exam_session.id, remaining_time=7200, saved_answers={})
                           
@app.route('/exam/resume')
@login_required
@vip_required
def resume_exam():
    user = get_current_user()
    exam_session = ExamSession.query.filter_by(user_id=user.id, submitted_at=None, cancelled=False).first()

    if not exam_session:
        flash('No active exam session found.', 'warning')
        return redirect(url_for('start_exam'))

    question_ids = session.get('exam_questions')
    if not question_ids:
        questions = get_questions_for_user(user)
        session['exam_questions'] = [q.id for q in questions]
    else:
        questions = Question.query.filter(Question.id.in_(question_ids)).all()
        id_to_q = {q.id: q for q in questions}
        questions = [id_to_q[qid] for qid in question_ids if qid in id_to_q]

    elapsed = (datetime.now(timezone.utc) - exam_session.started_at).total_seconds()
    remaining = max(0, 7200 - int(elapsed))

    if remaining == 0:
        return redirect(url_for('submit_exam_auto', session_id=exam_session.id))

    saved_answers = {ans.question_id: ans.selected_answer
                     for ans in UserAnswer.query.filter_by(session_id=exam_session.id).all()}

    # ✅ Convert questions to dicts for JSON serialization
    questions_data = [{
        'id': q.id,
        'question_text': q.question_text,
        'option_a': q.option_a,
        'option_b': q.option_b,
        'option_c': q.option_c,
        'option_d': q.option_d
    } for q in questions]

    return render_template('exam.html', user=user, questions=questions_data,
                           session_id=exam_session.id, saved_answers=saved_answers, remaining_time=remaining)
                           
@app.route('/exam/save-answer', methods=['POST'])
@login_required
def save_answer():
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        question_id = data.get('question_id')
        selected_answer = data.get('selected_answer')

        exam_session = db.session.get(ExamSession, session_id)
        if not exam_session or exam_session.user_id != session['user_id']:
            return jsonify({'error': 'Unauthorized'}), 401
        if exam_session.submitted_at:
            return jsonify({'error': 'Exam already submitted'}), 400

        exam_session.last_active_at = datetime.now(timezone.utc)

        answer = UserAnswer.query.filter_by(session_id=session_id, question_id=question_id).first()
        if not answer:
            answer = UserAnswer(session_id=session_id, question_id=question_id)
            db.session.add(answer)

        answer.selected_answer = selected_answer
        answer.saved_at = datetime.now(timezone.utc)
        db.session.commit()

        return jsonify({'success': True})
    except Exception:
        db.session.rollback()
        return jsonify({'error': 'Save failed'}), 500


@app.route('/exam/submit', methods=['POST'])
@login_required
def submit_exam():
    try:
        data = request.get_json()
        session_id = data.get('session_id')

        exam_session = db.session.get(ExamSession, session_id)
        if not exam_session or exam_session.user_id != session['user_id']:
            return jsonify({'error': 'Unauthorized'}), 401
        if exam_session.submitted_at:
            return jsonify({'error': 'Already submitted'}), 400

        answers = UserAnswer.query.filter_by(session_id=session_id).all()
        score = 0

        for ans in answers:
            question = db.session.get(Question, ans.question_id)
            if question:
                ans.is_correct = (ans.selected_answer == question.correct_answer)
                if ans.is_correct:
                    score += 1

                if not question.explanation:
                    options = {'A': question.option_a, 'B': question.option_b,
                               'C': question.option_c, 'D': question.option_d}
                    explanation = generate_explanation_with_groq(
                        question.question_text, options, question.correct_answer, question.subject
                    )
                    if explanation:
                        question.explanation = explanation

        exam_session.score = score
        exam_session.submitted_at = datetime.now(timezone.utc)
        exam_session.active_session_token = None

        user = db.session.get(User, session['user_id'])
        user.has_taken_exam = True

        db.session.commit()

        session.pop('exam_questions', None)
        session.pop('exam_session_id', None)
        session.pop('exam_start_time', None)

        flash(f'Exam submitted! Your score: {score}/{exam_session.total_questions}', 'success')
        return jsonify({'success': True, 'score': score, 'total': exam_session.total_questions})
    except Exception:
        db.session.rollback()
        return jsonify({'error': 'Submission failed'}), 500


@app.route('/exam/submit-auto/<session_id>')
@login_required
def submit_exam_auto(session_id):
    exam_session = db.session.get(ExamSession, session_id)
    if exam_session and exam_session.user_id == session['user_id'] and not exam_session.submitted_at:
        answers = UserAnswer.query.filter_by(session_id=session_id).all()
        score = sum(1 for ans in answers if ans.selected_answer == db.session.get(Question, ans.question_id).correct_answer)

        exam_session.score = score
        exam_session.submitted_at = datetime.now(timezone.utc)
        exam_session.active_session_token = None

        user = db.session.get(User, session['user_id'])
        user.has_taken_exam = True
        db.session.commit()

        flash('Time expired. Your exam has been submitted automatically.', 'warning')
    return redirect(url_for('result'))


@app.route('/exam/result')
@login_required
def result():
    user = get_current_user()
    exam_session = ExamSession.query.filter_by(user_id=user.id).order_by(ExamSession.submitted_at.desc()).first()

    if not exam_session or not exam_session.submitted_at:
        flash('No completed exam found.', 'info')
        return redirect(url_for('dashboard'))

    answers = UserAnswer.query.filter_by(session_id=exam_session.id).all()
    results = []
    for ans in answers:
        q = db.session.get(Question, ans.question_id)
        if q:
            results.append({
                'question': q.question_text,
                'subject': q.subject,
                'selected': ans.selected_answer,
                'correct': q.correct_answer,
                'is_correct': ans.is_correct,
                'explanation': q.explanation,
                'options': {'A': q.option_a, 'B': q.option_b, 'C': q.option_c, 'D': q.option_d}
            })

    return render_template('result.html', user=user, score=exam_session.score, total=exam_session.total_questions, results=results)


@app.route('/leaderboard')
def leaderboard():
    top_scores = db.session.query(User, ExamSession).join(ExamSession).filter(
        ExamSession.submitted_at.isnot(None)
    ).order_by(ExamSession.score.desc()).limit(10).all()
    return render_template('leaderboard.html', user=get_current_user(), top_scores=top_scores)


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        if request.form['password'] == os.environ.get('ADMIN_PASSWORD', 'admin123'):
            session['is_admin'] = True
            flash('Admin logged in successfully.', 'success')
            return redirect(url_for('admin_dashboard'))
        flash('Invalid admin password.', 'error')
    return render_template('admin/login.html', user=None)


@app.route('/admin/logout')
def admin_logout():
    session.pop('is_admin', None)
    flash('Admin logged out.', 'info')
    return redirect(url_for('index'))


@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    return render_template('admin/dashboard.html', user=get_current_user(),
                           total_users=User.query.count(),
                           vip_users=User.query.filter_by(is_vip=True).count(),
                           completed_exams=ExamSession.query.filter(ExamSession.submitted_at.isnot(None)).count(),
                           pending_vip=User.query.filter_by(is_vip=False).count(),
                           recent_users=User.query.order_by(User.created_at.desc()).limit(5).all())


@app.route('/admin/users')
@admin_required
def admin_users():
    return render_template('admin/users.html', user=get_current_user(),
                           users=User.query.order_by(User.created_at.desc()).all())


@app.route('/admin/make-vip/<user_id>')
@admin_required
def make_vip(user_id):
    if user := db.session.get(User, user_id):
        user.is_vip = True
        db.session.commit()
        flash(f'{user.full_name} is now VIP.', 'success')
    return redirect(url_for('admin_users'))


@app.route('/admin/remove-vip/<user_id>')
@admin_required
def remove_vip(user_id):
    if user := db.session.get(User, user_id):
        user.is_vip = False
        db.session.commit()
        flash(f'Removed VIP status from {user.full_name}.', 'success')
    return redirect(url_for('admin_users'))


@app.route('/admin/reset-exam/<user_id>')
@admin_required
def reset_exam(user_id):
    if user := db.session.get(User, user_id):
        user.has_taken_exam = False
        ExamSession.query.filter_by(user_id=user_id, submitted_at=None).update({'cancelled': True})
        db.session.commit()
        flash(f'Exam reset for {user.full_name}.', 'success')
    return redirect(url_for('admin_users'))


@app.route('/admin/results')
@admin_required
def admin_results():
    results = db.session.query(User, ExamSession).join(ExamSession).filter(
        ExamSession.submitted_at.isnot(None)
    ).order_by(ExamSession.score.desc()).all()
    return render_template('admin/results.html', user=get_current_user(), results=results)


@app.errorhandler(404)
def not_found(e):
    return render_template('404.html', user=get_current_user()), 404


@app.errorhandler(500)
def server_error(e):
    db.session.rollback()
    return render_template('500.html', user=get_current_user()), 500


@app.context_processor
def inject_globals():
    return dict(
        current_user=get_current_user(),
        founder_name=FOUNDER_NAME,
        founder_email=FOUNDER_EMAIL,
        founder_phone=FOUNDER_PHONE,
        founder_whatsapp=FOUNDER_WHATSAPP
    )


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=False, host='0.0.0.0', port=5000)
