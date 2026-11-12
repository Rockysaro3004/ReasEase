"""
Document management and reading assistant routes for ReadEase.
Handles PDF upload, reader interface, summarization, vocabulary, text-to-speech, and quizzes.
"""
import os
import json
from pathlib import Path
from flask import (
    Blueprint, render_template, redirect, url_for, flash,
    request, current_app, abort, jsonify, session
)
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Document, Summary, Vocabulary, QuizResult
from app.services.pdf_processor import PDFProcessor
from app.services.summarizer import ExtractiveSummarizer
from app.services.vocabulary import VocabularyExtractor
from app.services.quiz_generator import QuizGenerator

documents_bp = Blueprint('documents', __name__, url_prefix='/documents')


def get_user_document_or_404(doc_id):
    """
    Enforces strict access control: ensures the requested document exists
    AND belongs to the currently logged-in student.
    """
    doc = Document.query.get_or_404(doc_id)
    if doc.user_id != current_user.id:
        abort(403)  # Forbidden access to another student's document
    return doc


@documents_bp.route('/', methods=['GET'])
@login_required
def list_documents():
    """Lists all uploaded documents for the active student."""
    documents = Document.query.filter_by(user_id=current_user.id).order_by(Document.upload_date.desc()).all()
    return render_template('documents.html', title='My Documents - ReadEase', documents=documents)


@documents_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_document():
    """Handles PDF file upload, validation, and PyMuPDF text extraction."""
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part selected. Please select a PDF file.', 'danger')
            return redirect(request.url)

        file = request.files['file']
        if file.filename == '':
            flash('No file selected. Please choose a PDF file to upload.', 'danger')
            return redirect(request.url)

        if not PDFProcessor.allowed_file(file.filename):
            flash('Invalid file type! Only PDF (.pdf) documents are supported.', 'danger')
            return redirect(request.url)

        upload_folder = current_app.config['UPLOAD_FOLDER']
        stored_filename, save_path = PDFProcessor.save_file(file, upload_folder)

        # Extract text using PyMuPDF
        success, text_or_error, page_count = PDFProcessor.extract_text(save_path)

        if not success:
            # Delete stored file if text extraction could not proceed (e.g. scanned image PDF)
            try:
                os.remove(save_path)
            except OSError:
                pass
            flash(text_or_error, 'warning')
            return redirect(url_for('documents.upload_document'))

        # Save document record in SQLite
        doc = Document(
            user_id=current_user.id,
            original_filename=file.filename,
            stored_filename=stored_filename,
            extracted_text=text_or_error
        )
        db.session.add(doc)
        db.session.commit()

        flash(f'"{file.filename}" uploaded successfully! Extracted text from {page_count} page(s).', 'success')
        return redirect(url_for('documents.read_document', doc_id=doc.id))

    return render_template('documents.html', title='Upload Study Material - ReadEase', show_upload=True)


@documents_bp.route('/<int:doc_id>', methods=['GET'])
@login_required
def read_document(doc_id):
    """Clean reading interface with word count, reading time estimate, and TTS toolbar."""
    doc = get_user_document_or_404(doc_id)

    # Calculate reading metrics
    words = doc.extracted_text.split() if doc.extracted_text else []
    word_count = len(words)
    # Average student reading speed is ~200 words per minute
    estimated_mins = max(1, round(word_count / 200))

    summaries = Summary.query.filter_by(document_id=doc.id).order_by(Summary.created_at.desc()).all()
    quizzes = QuizResult.query.filter_by(document_id=doc.id).order_by(QuizResult.completed_at.desc()).all()

    return render_template(
        'reader.html',
        title=f'Reader: {doc.original_filename} - ReadEase',
        document=doc,
        word_count=word_count,
        estimated_mins=estimated_mins,
        summaries_count=len(summaries),
        quizzes_count=len(quizzes)
    )


@documents_bp.route('/<int:doc_id>/delete', methods=['POST'])
@login_required
def delete_document(doc_id):
    """Deletes document record, associated summaries/vocab/quizzes, and physical file."""
    doc = get_user_document_or_404(doc_id)
    doc_name = doc.original_filename

    # Delete physical file from storage
    file_path = Path(current_app.config['UPLOAD_FOLDER']) / doc.stored_filename
    if file_path.exists():
        try:
            os.remove(file_path)
        except OSError as e:
            current_app.logger.warning(f"Could not remove physical file {file_path}: {e}")

    db.session.delete(doc)
    db.session.commit()
    flash(f'Document "{doc_name}" has been deleted.', 'info')
    return redirect(url_for('documents.list_documents'))


@documents_bp.route('/<int:doc_id>/summary', methods=['GET', 'POST'])
@login_required
def document_summary(doc_id):
    """Extractive summarization interface with selectable length."""
    doc = get_user_document_or_404(doc_id)

    selected_length = request.form.get('length', 'medium')
    summary_result = None

    if request.method == 'POST':
        summary_result = ExtractiveSummarizer.generate_summary(doc.extracted_text, selected_length)

        # Save generated summary to database
        new_summary = Summary(
            document_id=doc.id,
            user_id=current_user.id,
            summary_text=summary_result['summary_text'],
            summary_length=selected_length
        )
        db.session.add(new_summary)
        db.session.commit()
        flash('New extractive summary generated and saved.', 'success')

    # Fetch previous summaries for this document
    saved_summaries = Summary.query.filter_by(document_id=doc.id).order_by(Summary.created_at.desc()).all()

    return render_template(
        'summary.html',
        title=f'Summary: {doc.original_filename} - ReadEase',
        document=doc,
        summary_result=summary_result,
        selected_length=selected_length,
        saved_summaries=saved_summaries
    )


@documents_bp.route('/<int:doc_id>/vocabulary', methods=['GET'])
@login_required
def document_vocabulary(doc_id):
    """Vocabulary assistant extracting challenging academic words with definitions."""
    doc = get_user_document_or_404(doc_id)
    vocab_items = VocabularyExtractor.extract_vocabulary(doc.extracted_text, max_words=20)

    # Check which words are already saved in the student's notebook
    saved_words = {
        v.word.lower(): v.id
        for v in Vocabulary.query.filter_by(user_id=current_user.id).all()
    }

    return render_template(
        'vocabulary.html',
        title=f'Vocabulary: {doc.original_filename} - ReadEase',
        document=doc,
        vocabulary_items=vocab_items,
        saved_words=saved_words
    )


@documents_bp.route('/vocabulary/save', methods=['POST'])
@login_required
def save_vocabulary():
    """Saves a vocabulary word to the student's personal vocabulary notebook."""
    doc_id = request.form.get('document_id')
    word = request.form.get('word', '').strip()
    meaning = request.form.get('meaning', '').strip()

    if not word:
        flash('Word cannot be empty.', 'danger')
        return redirect(request.referrer or url_for('documents.list_documents'))

    # Check for duplicate in user's notebook
    existing = Vocabulary.query.filter_by(user_id=current_user.id, word=word).first()
    if existing:
        flash(f'"{word}" is already saved in your vocabulary notebook.', 'info')
    else:
        vocab = Vocabulary(
            user_id=current_user.id,
            document_id=int(doc_id) if doc_id and doc_id.isdigit() else None,
            word=word,
            meaning=meaning
        )
        db.session.add(vocab)
        db.session.commit()
        flash(f'"{word}" saved to your personal vocabulary notebook!', 'success')

    return redirect(request.referrer or url_for('documents.list_documents'))


@documents_bp.route('/vocabulary', methods=['GET'])
@login_required
def personal_vocabulary():
    """Displays student's entire personal saved vocabulary notebook."""
    saved_items = Vocabulary.query.filter_by(user_id=current_user.id).order_by(Vocabulary.created_at.desc()).all()
    return render_template('personal_vocabulary.html', title='My Vocabulary Notebook - ReadEase', items=saved_items)


@documents_bp.route('/vocabulary/<int:vocab_id>/delete', methods=['POST'])
@login_required
def delete_vocabulary(vocab_id):
    """Deletes a word from the student's personal vocabulary notebook."""
    vocab = Vocabulary.query.get_or_404(vocab_id)
    if vocab.user_id != current_user.id:
        abort(403)
    word_name = vocab.word
    db.session.delete(vocab)
    db.session.commit()
    flash(f'Removed "{word_name}" from your vocabulary notebook.', 'info')
    return redirect(url_for('documents.personal_vocabulary'))


@documents_bp.route('/<int:doc_id>/quiz', methods=['GET', 'POST'])
@login_required
def document_quiz(doc_id):
    """Interactive rule-based quiz generation, evaluation, and scoring."""
    doc = get_user_document_or_404(doc_id)

    if request.method == 'POST':
        # Retrieve generated quiz questions from session to grade against
        quiz_json = session.get(f'quiz_questions_{doc.id}')
        if not quiz_json:
            flash('Quiz session expired. Generating a fresh quiz.', 'warning')
            return redirect(url_for('documents.document_quiz', doc_id=doc.id))

        questions = json.loads(quiz_json)
        submitted_answers = request.form.to_dict()

        # Grade quiz
        evaluation = QuizGenerator.evaluate_quiz(questions, submitted_answers)

        # Save result to database
        quiz_result = QuizResult(
            user_id=current_user.id,
            document_id=doc.id,
            score=evaluation['score'],
            total_questions=evaluation['total']
        )
        db.session.add(quiz_result)
        db.session.commit()

        # Clear session
        session.pop(f'quiz_questions_{doc.id}', None)

        flash(f'Quiz completed! You scored {evaluation["score"]} out of {evaluation["total"]} ({evaluation["percentage"]}%).', 'success')

        return render_template(
            'quiz_result.html',
            title=f'Quiz Result: {doc.original_filename} - ReadEase',
            document=doc,
            evaluation=evaluation,
            result_record=quiz_result
        )

    # GET request: Generate questions and store in session
    questions = QuizGenerator.generate_quiz(doc.extracted_text, num_questions=5)
    session[f'quiz_questions_{doc.id}'] = json.dumps(questions)

    past_attempts = QuizResult.query.filter_by(
        user_id=current_user.id,
        document_id=doc.id
    ).order_by(QuizResult.completed_at.desc()).all()

    return render_template(
        'quiz.html',
        title=f'Quick Quiz: {doc.original_filename} - ReadEase',
        document=doc,
        questions=questions,
        past_attempts=past_attempts
    )


@documents_bp.route('/<int:doc_id>/tts', methods=['GET'])
@login_required
def text_to_speech(doc_id):
    """Dedicated Text-to-Speech listening room with speed controls and speech synthesis."""
    doc = get_user_document_or_404(doc_id)
    return render_template(
        'tts_reader.html',
        title=f'Audio Reader: {doc.original_filename} - ReadEase',
        document=doc
    )
