"""
Quiz Generation Service
Generates simple rule-based multiple-choice questions directly from source study material.
Strictly grounded in extracted text with verifiable source explanations.
"""
import re
import random
from collections import Counter

try:
    from app.services.summarizer import ExtractiveSummarizer, STOPWORDS
except ImportError:
    from summarizer import ExtractiveSummarizer, STOPWORDS


class QuizGenerator:
    """Generates and evaluates multiple-choice questions from document text."""

    DEFINITION_PATTERNS = [
        r'\b([A-Z][a-zA-Z\s]{2,25})\s+is\s+(?:defined\s+as\s+|a\s+|an\s+|the\s+)([^.?!]{15,120})[.?!]',
        r'\b([A-Z][a-zA-Z\s]{2,25})\s+refers\s+to\s+([^.?!]{15,120})[.?!]',
        r'\b([A-Z][a-zA-Z\s]{2,25})\s+are\s+(?:defined\s+as\s+|the\s+|considered\s+)([^.?!]{15,120})[.?!]',
        r'\b([A-Z][a-zA-Z\s]{2,25})\s+plays\s+a\s+(?:key|vital|critical|central)\s+role\s+in\s+([^.?!]{15,120})[.?!]'
    ]

    @classmethod
    def extract_key_terms(cls, text):
        """Extracts prominent nouns/proper nouns and capitalized multi-word terms."""
        capitalized = re.findall(r'\b[A-Z][a-z]{3,}(?:\s+[A-Z][a-z]{3,})?\b', text)
        all_words = re.findall(r'\b[a-zA-Z]{5,}\b', text)
        
        content_words = [w.capitalize() for w in all_words if w.lower() not in STOPWORDS]
        word_counts = Counter(content_words + capitalized)
        return [word for word, count in word_counts.most_common(40)]

    @classmethod
    def generate_quiz(cls, text, num_questions=5):
        """
        Extracts up to num_questions multiple choice questions from text.
        Each question is grounded in a specific sentence in the document.
        """
        sentences = ExtractiveSummarizer.split_into_sentences(text)
        if len(sentences) < 3:
            return []

        key_terms = cls.extract_key_terms(text)
        questions = []
        used_sentences = set()

        # Strategy 1: Look for explicit definition patterns
        for pattern in cls.DEFINITION_PATTERNS:
            for match in re.finditer(pattern, text):
                term = match.group(1).strip()
                description = match.group(2).strip()

                if len(term.split()) <= 4 and term not in STOPWORDS and len(term) >= 3:
                    full_match = match.group(0).strip()
                    if full_match in used_sentences:
                        continue
                    used_sentences.add(full_match)

                    distractors = [k for k in key_terms if k.lower() != term.lower() and len(k) >= 3]
                    if len(distractors) < 3:
                        distractors += ["Theoretical Model", "Empirical Method", "Variable Factor"]

                    options = random.sample(distractors, min(3, len(distractors)))
                    options.append(term)
                    random.shuffle(options)

                    questions.append({
                        'id': len(questions) + 1,
                        'question': f"Based on the study material, which concept is described as: \"...{description}\"?",
                        'options': options,
                        'correct_answer': term,
                        'explanation': f"Source statement: \"{full_match}\""
                    })

                    if len(questions) >= num_questions:
                        return questions

        # Strategy 2: Cloze / Fill-in-the-blank on high-salience sentences
        for sentence in sentences:
            if sentence in used_sentences or len(sentence.split()) < 8:
                continue

            sentence_words = [w for w in re.findall(r'\b[a-zA-Z]{5,}\b', sentence) if w.lower() not in STOPWORDS]
            if not sentence_words:
                continue

            target_word = max(sentence_words, key=lambda w: len(w))
            target_cap = target_word.capitalize()

            pattern = re.compile(rf'\b{re.escape(target_word)}\b', re.IGNORECASE)
            masked_sentence = pattern.sub("__________", sentence, count=1)

            distractors = [k for k in key_terms if k.lower() != target_word.lower() and len(k) >= 4]
            if len(distractors) < 3:
                distractors += ["Framework", "Hypothesis", "System", "Analysis"]

            options = random.sample(distractors, min(3, len(distractors)))
            options.append(target_cap)
            random.shuffle(options)

            used_sentences.add(sentence)
            questions.append({
                'id': len(questions) + 1,
                'question': f"Fill in the blank from the reading: \"{masked_sentence}\"",
                'options': options,
                'correct_answer': target_cap,
                'explanation': f"Original sentence: \"{sentence}\""
            })

            if len(questions) >= num_questions:
                break

        return questions

    @classmethod
    def evaluate_quiz(cls, questions_data, submitted_answers):
        """
        Evaluates submitted student answers against the generated questions.
        Returns a dictionary with score, total, percentage, and detailed feedback per question.
        """
        score = 0
        total = len(questions_data)
        detailed_feedback = []

        for q in questions_data:
            q_id = str(q['id'])
            user_choice = submitted_answers.get(q_id, '').strip()
            correct = q['correct_answer'].strip()
            is_correct = (user_choice.lower() == correct.lower())

            if is_correct:
                score += 1

            detailed_feedback.append({
                'question_id': q['id'],
                'question': q['question'],
                'user_choice': user_choice if user_choice else "No answer submitted",
                'correct_answer': correct,
                'is_correct': is_correct,
                'explanation': q['explanation']
            })

        percentage = round((score / max(total, 1)) * 100, 1)

        return {
            'score': score,
            'total': total,
            'percentage': percentage,
            'feedback': detailed_feedback
        }
