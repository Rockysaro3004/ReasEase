"""
Unit test suite for ReadEase core algorithmic services and logic.
Run with:
    python3 tests/test_services.py
"""
import unittest
import sys
import importlib.util
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Dynamically load modules directly to avoid importing Flask in non-Flask test environments
def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

summarizer_mod = load_module("summarizer", BASE_DIR / "app" / "services" / "summarizer.py")
vocab_mod = load_module("vocabulary", BASE_DIR / "app" / "services" / "vocabulary.py")
quiz_mod = load_module("quiz_generator", BASE_DIR / "app" / "services" / "quiz_generator.py")

ExtractiveSummarizer = summarizer_mod.ExtractiveSummarizer
VocabularyExtractor = vocab_mod.VocabularyExtractor
QuizGenerator = quiz_mod.QuizGenerator


class TestCoreServices(unittest.TestCase):
    """Verifies text summarization, vocabulary extraction, and quiz generation."""

    def setUp(self):
        self.sample_text = (
            "Photosynthesis is the process used by green plants and certain other organisms "
            "to synthesize nutrients from carbon dioxide and water. Photosynthesis in plants "
            "generally involves the green pigment chlorophyll and generates oxygen as a byproduct. "
            "Mitochondria are membrane-bound cell organelles that generate most of the chemical "
            "energy needed to power the cell's biochemical reactions. Chemical energy produced by "
            "the mitochondria is stored in a small molecule called adenosine triphosphate. "
            "An algorithm is defined as a step-by-step procedure for solving a mathematical "
            "or computational problem."
        )

    def test_extractive_summarizer_sentence_split(self):
        """Tests that text is accurately parsed into sentences."""
        sentences = ExtractiveSummarizer.split_into_sentences(self.sample_text)
        self.assertGreaterEqual(len(sentences), 4)

    def test_extractive_summarizer_length_modes(self):
        """Tests summarization under short, medium, and long configurations."""
        short_summary = ExtractiveSummarizer.generate_summary(self.sample_text, 'short')
        medium_summary = ExtractiveSummarizer.generate_summary(self.sample_text, 'medium')

        self.assertIn('summary_text', short_summary)
        self.assertGreater(len(short_summary['summary_text']), 0)
        self.assertLessEqual(short_summary['sentence_count'], medium_summary['sentence_count'])
        self.assertGreater(short_summary['reduction_pct'], 0)

    def test_vocabulary_extractor(self):
        """Tests academic vocabulary extraction and dictionary matching."""
        vocab = VocabularyExtractor.extract_vocabulary(self.sample_text, max_words=10)
        self.assertIsInstance(vocab, list)
        self.assertGreater(len(vocab), 0)

        extracted_words = [item['word'].lower() for item in vocab]
        self.assertTrue(any(w in extracted_words for w in ['synthesize', 'algorithm', 'mitochondria', 'process']))

    def test_quiz_generator_and_evaluator(self):
        """Tests rule-based question generation and grading."""
        questions = QuizGenerator.generate_quiz(self.sample_text, num_questions=3)
        self.assertGreaterEqual(len(questions), 1)

        first_q = questions[0]
        self.assertIn('question', first_q)
        self.assertIn('options', first_q)
        self.assertEqual(len(first_q['options']), 4)
        self.assertIn(first_q['correct_answer'], first_q['options'])
        self.assertIn('explanation', first_q)

        # Test evaluation with correct answer
        user_answers = {str(first_q['id']): first_q['correct_answer']}
        eval_result = QuizGenerator.evaluate_quiz([first_q], user_answers)
        self.assertEqual(eval_result['score'], 1)
        self.assertEqual(eval_result['percentage'], 100.0)


if __name__ == '__main__':
    unittest.main()
