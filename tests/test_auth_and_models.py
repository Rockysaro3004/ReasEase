"""
Unit tests for ReadEase database models and password security.
Run inside virtual environment:
    python -m unittest tests/test_auth_and_models.py
"""
import unittest
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

try:
    from app import create_app
    from app.extensions import db
    from app.models import User, Document, Summary, Vocabulary, QuizResult
    HAS_FLASK = True
except ImportError:
    HAS_FLASK = False


@unittest.skipUnless(HAS_FLASK, "Flask and Flask-SQLAlchemy required in environment")
class TestUserModel(unittest.TestCase):
    """Tests password hashing, verification, and reset tokens."""

    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_password_hashing(self):
        """Verifies passwords are never stored plain-text and hash validates."""
        u = User(full_name="Test Student", email="test@student.edu")
        u.set_password("MySecurePass123")
        db.session.add(u)
        db.session.commit()

        self.assertNotEqual(u.password_hash, "MySecurePass123")
        self.assertTrue(u.check_password("MySecurePass123"))
        self.assertFalse(u.check_password("WrongPassword"))

    def test_reset_token(self):
        """Verifies generation and validation of password reset tokens."""
        u = User(full_name="Token Tester", email="token@student.edu")
        u.set_password("OldPassword123")
        db.session.add(u)
        db.session.commit()

        token = u.get_reset_token()
        self.assertIsNotNone(token)

        verified_user = User.verify_reset_token(token)
        self.assertEqual(verified_user.id, u.id)

    def test_user_document_relationship(self):
        """Verifies foreign key relationships and user-specific document storage."""
        u = User(full_name="Author Student", email="author@student.edu")
        u.set_password("Pass123")
        db.session.add(u)
        db.session.commit()

        doc = Document(
            user_id=u.id,
            original_filename="Lecture1.pdf",
            stored_filename="unique_lec1.pdf",
            extracted_text="Sample lecture content."
        )
        db.session.add(doc)
        db.session.commit()

        self.assertEqual(len(u.documents), 1)
        self.assertEqual(u.documents[0].original_filename, "Lecture1.pdf")


if __name__ == '__main__':
    unittest.main()
