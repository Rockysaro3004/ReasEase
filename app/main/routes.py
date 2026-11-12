"""
Main routes for ReadEase
Handles landing page, personalized dashboard, and student profile.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Document, Summary, Vocabulary, QuizResult

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def landing():
    """Public landing page showcasing ReadEase value proposition and features."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('landing.html', title='ReadEase – Smart Reading Assistant for Students')


@main_bp.route('/dashboard')
@login_required
def dashboard():
    """
    Student dashboard displaying personalized metrics, recent documents,
    study progress, and quick access to reading tools.
    """
    # Fetch student-specific records strictly scoped to current_user
    user_docs = Document.query.filter_by(user_id=current_user.id).order_by(Document.upload_date.desc()).all()
    user_summaries = Summary.query.filter_by(user_id=current_user.id).order_by(Summary.created_at.desc()).all()
    user_vocab = Vocabulary.query.filter_by(user_id=current_user.id).order_by(Vocabulary.created_at.desc()).all()
    user_quizzes = QuizResult.query.filter_by(user_id=current_user.id).order_by(QuizResult.completed_at.desc()).all()

    # Aggregate metric counters
    total_docs = len(user_docs)
    total_summaries = len(user_summaries)
    total_vocab = len(user_vocab)
    total_quizzes = len(user_quizzes)

    # Calculate average quiz accuracy
    avg_score = 0
    if total_quizzes > 0:
        total_earned = sum(q.score for q in user_quizzes)
        total_possible = sum(q.total_questions for q in user_quizzes)
        if total_possible > 0:
            avg_score = round((total_earned / total_possible) * 100, 1)

    recent_docs = user_docs[:5]
    recent_quizzes = user_quizzes[:5]

    return render_template(
        'dashboard.html',
        title='Dashboard - ReadEase',
        total_docs=total_docs,
        total_summaries=total_summaries,
        total_vocab=total_vocab,
        total_quizzes=total_quizzes,
        avg_score=avg_score,
        recent_docs=recent_docs,
        recent_quizzes=recent_quizzes
    )


@main_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Student profile page displaying account details and password change."""
    if request.method == 'POST':
        new_name = request.form.get('full_name', '').strip()
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Update name if provided
        if new_name and new_name != current_user.full_name:
            current_user.full_name = new_name
            db.session.commit()
            flash('Your profile name has been updated.', 'success')

        # Handle password change
        if new_password:
            if not current_user.check_password(current_password):
                flash('Your current password was incorrect.', 'danger')
            elif len(new_password) < 6:
                flash('New password must be at least 6 characters.', 'danger')
            elif new_password != confirm_password:
                flash('New passwords do not match.', 'danger')
            else:
                current_user.set_password(new_password)
                db.session.commit()
                flash('Your password has been changed successfully.', 'success')

        return redirect(url_for('main.profile'))

    total_docs = Document.query.filter_by(user_id=current_user.id).count()
    total_summaries = Summary.query.filter_by(user_id=current_user.id).count()
    total_quizzes = QuizResult.query.filter_by(user_id=current_user.id).count()
    total_vocab = Vocabulary.query.filter_by(user_id=current_user.id).count()

    return render_template(
        'profile.html',
        title='My Profile - ReadEase',
        total_docs=total_docs,
        total_summaries=total_summaries,
        total_quizzes=total_quizzes,
        total_vocab=total_vocab
    )
