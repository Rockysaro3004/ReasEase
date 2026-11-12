"""
Vocabulary Extraction Service
Analyzes document text to detect academic and challenging vocabulary.
Includes a built-in curated educational dictionary and optional fallback to DictionaryAPI.
"""
import re
import urllib.request
import urllib.parse
import json
from collections import Counter

try:
    from app.services.summarizer import STOPWORDS
except ImportError:
    from summarizer import STOPWORDS

# Curated dictionary of common academic & collegiate terminology
CURATED_DICTIONARY = {
    'analysis': {'pos': 'noun', 'meaning': 'A detailed examination of the elements or structure of something.', 'example': 'The statistical analysis confirmed our initial hypothesis.'},
    'approach': {'pos': 'noun', 'meaning': 'A way of dealing with something or a path towards a solution.', 'example': 'We adopted an innovative approach to solve the problem.'},
    'concept': {'pos': 'noun', 'meaning': 'An abstract idea or a general notion that represents a class of objects or events.', 'example': 'The fundamental concept of thermodynamics was introduced.'},
    'context': {'pos': 'noun', 'meaning': 'The circumstances that form the setting for an event, statement, or idea.', 'example': 'Quotations must be examined in their historical context.'},
    'criteria': {'pos': 'noun', 'meaning': 'Principles or standards by which something may be judged or decided.', 'example': 'The candidates fulfilled all the necessary evaluation criteria.'},
    'data': {'pos': 'noun', 'meaning': 'Facts, statistics, or items of information gathered for analysis.', 'example': 'The experimental data supported the researcher\'s claims.'},
    'definition': {'pos': 'noun', 'meaning': 'A statement of the exact meaning of a word, phrase, or concept.', 'example': 'The textbook provided a precise definition of photosynthesis.'},
    'empirical': {'pos': 'adjective', 'meaning': 'Based on, concerned with, or verifiable by observation or experience rather than theory.', 'example': 'The paper provided strong empirical evidence.'},
    'evaluate': {'pos': 'verb', 'meaning': 'To form an idea of the amount, number, or value of something; assess.', 'example': 'Instructors will evaluate the assignments based on clarity.'},
    'evidence': {'pos': 'noun', 'meaning': 'The available body of facts or information indicating whether a belief is valid.', 'example': 'Forensic evidence pointed toward a clear conclusion.'},
    'factor': {'pos': 'noun', 'meaning': 'A circumstance, fact, or influence that contributes to a result.', 'example': 'Temperature was a key factor in the chemical reaction.'},
    'framework': {'pos': 'noun', 'meaning': 'A basic structure underlying a system, concept, or text.', 'example': 'The theoretical framework guided the entire research study.'},
    'fundamental': {'pos': 'adjective', 'meaning': 'Forming a necessary base or core; of central importance.', 'example': 'Understanding algebra is fundamental to mastering calculus.'},
    'hypothesis': {'pos': 'noun', 'meaning': 'A proposed explanation made on the basis of limited evidence as a starting point for investigation.', 'example': 'The research tested the hypothesis that sleep improves memory.'},
    'implementation': {'pos': 'noun', 'meaning': 'The process of putting a decision or plan into effect; execution.', 'example': 'The swift implementation of the new policy prevented delays.'},
    'implication': {'pos': 'noun', 'meaning': 'The conclusion that can be drawn from something although not explicitly stated.', 'example': 'The discovery has profound implications for medicine.'},
    'methodology': {'pos': 'noun', 'meaning': 'A system of methods used in a particular area of study or activity.', 'example': 'The scientist described the research methodology in detail.'},
    'paradigm': {'pos': 'noun', 'meaning': 'A typical example or pattern of something; a model or overarching framework.', 'example': 'Quantum mechanics introduced a major paradigm shift in physics.'},
    'perspective': {'pos': 'noun', 'meaning': 'A particular attitude toward or way of regarding something; a point of view.', 'example': 'The issue was debated from multiple socio-economic perspectives.'},
    'principle': {'pos': 'noun', 'meaning': 'A fundamental truth or proposition serving as the foundation for a system of belief.', 'example': 'Conservation of energy is a core principle in natural sciences.'},
    'procedure': {'pos': 'noun', 'meaning': 'An established or official way of doing something.', 'example': 'Standard laboratory safety procedures must be observed at all times.'},
    'quantitative': {'pos': 'adjective', 'meaning': 'Relating to, measuring, or measured by the quantity of something rather than its quality.', 'example': 'Quantitative analysis relies on numerical calculations.'},
    'qualitative': {'pos': 'adjective', 'meaning': 'Relating to or measuring by the quality of something rather than its quantity.', 'example': 'Interviews provided rich qualitative insights into student experiences.'},
    'significant': {'pos': 'adjective', 'meaning': 'Sufficiently great or important to be worthy of attention; noteworthy.', 'example': 'There was a statistically significant difference between the test groups.'},
    'structure': {'pos': 'noun', 'meaning': 'The arrangement of and relations between the parts or elements of something complex.', 'example': 'The molecular structure determines the chemical properties.'},
    'synthesize': {'pos': 'verb', 'meaning': 'To combine a number of things into a coherent whole.', 'example': 'The student successfully synthesized three different academic arguments.'},
    'systematic': {'pos': 'adjective', 'meaning': 'Done or acting according to a fixed plan or system; methodical.', 'example': 'A systematic review of the literature was conducted.'},
    'theory': {'pos': 'noun', 'meaning': 'A supposition or a system of ideas intended to explain something.', 'example': 'Einstein\'s theory of relativity revolutionized physics.'},
    'variable': {'pos': 'noun', 'meaning': 'An element, feature, or factor that is liable to vary or change.', 'example': 'In this experiment, humidity was the independent variable.'}
}


class VocabularyExtractor:
    """Extracts difficult or frequent academic terms and retrieves definitions."""

    @staticmethod
    def fetch_online_definition(word):
        """
        Attempts to fetch meaning from the free public DictionaryAPI.
        Returns (meaning, pos, example) or (None, None, None) on timeout or failure.
        """
        try:
            url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{urllib.parse.quote(word)}"
            req = urllib.request.Request(
                url,
                headers={'User-Agent': 'ReadEase-Educational-App/1.0'}
            )
            with urllib.request.urlopen(req, timeout=1.5) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    if data and isinstance(data, list):
                        meanings = data[0].get('meanings', [])
                        if meanings:
                            first_meaning = meanings[0]
                            pos = first_meaning.get('partOfSpeech', 'noun')
                            defs = first_meaning.get('definitions', [])
                            if defs:
                                return (
                                    defs[0].get('definition', ''),
                                    pos,
                                    defs[0].get('example', '')
                                )
        except Exception:
            pass
        return None, None, None

    @classmethod
    def extract_vocabulary(cls, text, max_words=20):
        """
        Extracts candidate vocabulary terms from text.
        Filters out common short words and stopwords, prioritizing academic and multi-syllable terms.
        """
        words = re.findall(r'\b[a-zA-Z]{5,}\b', text.lower())
        filtered_words = [w for w in words if w not in STOPWORDS]

        counts = Counter(filtered_words)
        if not counts:
            return []

        # Sort candidate words by a combination of frequency and word length
        candidate_words = sorted(
            counts.keys(),
            key=lambda w: (counts[w] * 2) + len(w),
            reverse=True
        )[:max_words]

        vocabulary_list = []
        for word in candidate_words:
            freq = counts[word]

            # 1. Check curated educational dictionary
            if word in CURATED_DICTIONARY:
                info = CURATED_DICTIONARY[word]
                vocabulary_list.append({
                    'word': word.capitalize(),
                    'frequency': freq,
                    'part_of_speech': info['pos'],
                    'meaning': info['meaning'],
                    'example': info['example'],
                    'source': 'Curated Academic Lexicon'
                })
            else:
                # 2. Try online dictionary API fallback
                online_def, pos, example = cls.fetch_online_definition(word)
                if online_def:
                    vocabulary_list.append({
                        'word': word.capitalize(),
                        'frequency': freq,
                        'part_of_speech': pos or 'term',
                        'meaning': online_def,
                        'example': example or f"Refer to the document context for '{word}'.",
                        'source': 'Dictionary API'
                    })
                else:
                    # 3. Transparent fallback without inventing meanings
                    vocabulary_list.append({
                        'word': word.capitalize(),
                        'frequency': freq,
                        'part_of_speech': 'specialized term',
                        'meaning': 'Definition unavailable in offline lexicon. Check document context.',
                        'example': f"Appears {freq} time(s) in this study material.",
                        'source': 'Document Analysis'
                    })

        return vocabulary_list
