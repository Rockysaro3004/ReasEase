"""
Authentication routes for ReadEase
Handles registration, login, logout, and password recovery.
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, current_user, login_required
from urllib.parse import urlsplit
from app.extensions import db
from app.models import User
from app.auth.forms import RegistrationForm, LoginForm, RequestResetForm, ResetPasswordForm

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


def send_reset_email(user, reset_url):
    """
    Sends a password reset email if SMTP is configured.
    Returns (True, "sent message") or (False, "error message or dev notice").
    """
    mail_server = current_app.config.get('MAIL_SERVER')
    mail_username = current_app.config.get('MAIL_USERNAME')
    mail_password = current_app.config.get('MAIL_PASSWORD')
    
    # If SMTP is not configured, inform safely without claiming an email was sent
    if not (mail_server and mail_username and mail_password):
        current_app.logger.info(f"[LOCAL DEV MODE] Password reset link for {user.email}: {reset_url}")
        return False, "SMTP is not configured on this server. Running in local development mode."

    try:
        port = current_app.config.get('MAIL_PORT', 587)
        use_tls = current_app.config.get('MAIL_USE_TLS', True)
        sender = current_app.config.get('MAIL_DEFAULT_SENDER', mail_username)

        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'ReadEase - Password Reset Request'
        msg['From'] = sender
        msg['To'] = user.email

        text_content = f"""Hello {user.full_name},

You recently requested to reset your password for your ReadEase account.
Please visit the following link to reset your password:

{reset_url}

This link is valid for 1 hour. If you did not request this, please ignore this email.

Best regards,
The ReadEase Team
"""
        msg.attach(MIMEText(text_content, 'plain'))

        server = smtplib.SMTP(mail_server, port, timeout=10)
        if use_tls:
            server.starttls()
        server.login(mail_username, mail_password)
        server.sendmail(sender, [user.email], msg.as_string())
        server.quit()
        return True, "Email sent successfully."
    except Exception as e:
        current_app.logger.error(f"Failed to send reset email: {str(e)}")
        return False, f"Could not connect to SMTP server: {str(e)}"


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Student registration endpoint."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            full_name=form.full_name.data.strip(),
            email=form.email.data.lower().strip()
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        flash('Your account has been created successfully! You can now log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', title='Register - ReadEase', form=form)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Student login endpoint."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            flash(f'Welcome back, {user.full_name}!', 'success')

            # Prevent Open Redirect vulnerabilities
            next_page = request.args.get('next')
            if not next_page or urlsplit(next_page).netloc != '':
                next_page = url_for('main.dashboard')
            return redirect(next_page)
        else:
            flash('Login unsuccessful. Please check your email and password.', 'danger')

    return render_template('auth/login.html', title='Log In - ReadEase', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    """Student logout endpoint."""
    logout_user()
    flash('You have been logged out securely.', 'info')
    return redirect(url_for('main.landing'))


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Password reset request endpoint."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    form = RequestResetForm()
    dev_reset_url = None

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()
        if user:
            token = user.get_reset_token()
            reset_url = url_for('auth.reset_password', token=token, _external=True)
            sent, message = send_reset_email(user, reset_url)

            if sent:
                flash('An email has been sent with instructions to reset your password.', 'info')
                return redirect(url_for('auth.login'))
            else:
                # Safe local development mode: show the link directly on screen for testing
                dev_reset_url = reset_url
                flash(
                    'Local Development Mode: SMTP email is not configured. '
                    'Use the generated reset link shown below to test the password reset flow.',
                    'warning'
                )
        else:
            flash('No account found with that email address. Please check and try again.', 'danger')

    return render_template(
        'auth/forgot_password.html',
        title='Forgot Password - ReadEase',
        form=form,
        dev_reset_url=dev_reset_url
    )


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Token-based password reset completion endpoint."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    user = User.verify_reset_token(token)
    if user is None:
        flash('The password reset link is invalid or has expired. Please request a new one.', 'warning')
        return redirect(url_for('auth.forgot_password'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been updated! You can now log in with your new password.', 'success')
        return redirect(url_for('auth.login'))

    return render_template(
        'auth/reset_password.html',
        title='Reset Password - ReadEase',
        form=form
    )
