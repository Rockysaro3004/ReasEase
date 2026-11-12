"""
WTForms definitions for user authentication and password management.
"""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from app.models import User


class RegistrationForm(FlaskForm):
    """Student registration form with validation."""
    full_name = StringField(
        'Full Name',
        validators=[
            DataRequired(message="Please enter your full name."),
            Length(min=2, max=100, message="Name must be between 2 and 100 characters.")
        ]
    )
    email = StringField(
        'Email Address',
        validators=[
            DataRequired(message="Please enter your email address."),
            Email(message="Please enter a valid email address.")
        ]
    )
    password = PasswordField(
        'Password',
        validators=[
            DataRequired(message="Please enter a password."),
            Length(min=6, max=64, message="Password must be at least 6 characters.")
        ]
    )
    confirm_password = PasswordField(
        'Confirm Password',
        validators=[
            DataRequired(message="Please confirm your password."),
            EqualTo('password', message="Passwords must match.")
        ]
    )
    submit = SubmitField('Create Account')

    def validate_email(self, field):
        """Ensures email is not already registered."""
        user = User.query.filter_by(email=field.data.lower().strip()).first()
        if user:
            raise ValidationError('This email address is already registered. Please log in or use a different email.')


class LoginForm(FlaskForm):
    """User login form."""
    email = StringField(
        'Email Address',
        validators=[
            DataRequired(message="Please enter your email address."),
            Email(message="Please enter a valid email address.")
        ]
    )
    password = PasswordField(
        'Password',
        validators=[DataRequired(message="Please enter your password.")]
    )
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Log In')


class RequestResetForm(FlaskForm):
    """Form to initiate password reset via email."""
    email = StringField(
        'Registered Email Address',
        validators=[
            DataRequired(message="Please enter your email address."),
            Email(message="Please enter a valid email address.")
        ]
    )
    submit = SubmitField('Send Password Reset Link')


class ResetPasswordForm(FlaskForm):
    """Form to submit a new password using token."""
    password = PasswordField(
        'New Password',
        validators=[
            DataRequired(message="Please enter a new password."),
            Length(min=6, max=64, message="Password must be at least 6 characters.")
        ]
    )
    confirm_password = PasswordField(
        'Confirm New Password',
        validators=[
            DataRequired(message="Please confirm your new password."),
            EqualTo('password', message="Passwords must match.")
        ]
    )
    submit = SubmitField('Reset Password')
