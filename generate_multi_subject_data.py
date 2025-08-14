#!/usr/bin/env python3
"""
Multi-Subject Synthetic Training Data Generator for SnapGrade

This script generates synthetic training data across multiple academic subjects
including Math, Science, History, Literature, Geography, and more.
"""

import json
import random
import argparse
from typing import List, Dict, Tuple

class MultiSubjectDataGenerator:
    def __init__(self):
        self.subjects = {
            'math': self.generate_math_problems,
            'science': self.generate_science_problems,
            'history': self.generate_history_problems,
            'literature': self.generate_literature_problems,
            'geography': self.generate_geography_problems,
            'chemistry': self.generate_chemistry_problems,
            'physics': self.generate_physics_problems,
            'biology': self.generate_biology_problems,
            'english': self.generate_english_problems,
            'economics': self.generate_economics_problems
        }
    
    def generate_math_problems(self, count: int) -> List[Dict]:
        """Generate math problems"""
        problems = []
        math_topics = [
            ('algebra', 'Solve for x: 2x + 5 = 13', 'x = 4', 'Show all algebraic steps clearly'),
            ('geometry', 'Find the area of a triangle with base 8cm and height 6cm', '24 cm²', 'Use the formula A = (1/2) × base × height'),
            ('calculus', 'Find the derivative of f(x) = 3x² + 2x - 1', "f'(x) = 6x + 2", 'Apply power rule and constant rule'),
            ('statistics', 'Calculate the mean of: 4, 7, 9, 12, 8', '8', 'Sum all values and divide by count'),
            ('trigonometry', 'Find sin(30°)', '1/2 or 0.5', 'Use unit circle or special triangles')
        ]
        
        for i in range(count):
            topic, question, answer, rubric = random.choice(math_topics)
            score = random.choice(['8/10', '9/10', '7/10', '10/10', '6/10'])
            feedback = f"Good work on {topic}. {rubric}. Consider showing more detailed steps."
            
            problems.append({
                'submission': answer,
                'rubric': f"{topic.title()} Problem: {question}. {rubric}",
                'score': score,
                'feedback': feedback
            })
        return problems
    
    def generate_science_problems(self, count: int) -> List[Dict]:
        """Generate general science problems"""
        problems = []
        science_topics = [
            ('photosynthesis', 'Explain the process of photosynthesis', 'Plants convert sunlight, CO2, and water into glucose and oxygen', 'Include reactants, products, and location'),
            ('gravity', 'What is gravity?', 'A fundamental force that attracts objects with mass', 'Explain universal nature and effects'),
            ('atoms', 'Describe the structure of an atom', 'Nucleus with protons/neutrons, electrons in orbitals', 'Include all subatomic particles'),
            ('evolution', 'Define natural selection', 'Process where organisms with favorable traits survive and reproduce', 'Mention Darwin and adaptation'),
            ('ecosystems', 'What is a food chain?', 'Series showing energy transfer from producers to consumers', 'Include trophic levels')
        ]
        
        for i in range(count):
            topic, question, answer, rubric = random.choice(science_topics)
            score = random.choice(['8/10', '9/10', '7/10', '10/10', '6/10'])
            feedback = f"Good understanding of {topic}. {rubric}. Add more scientific detail."
            
            problems.append({
                'submission': answer,
                'rubric': f"Science Question: {question}. {rubric}",
                'score': score,
                'feedback': feedback
            })
        return problems
    
    def generate_history_problems(self, count: int) -> List[Dict]:
        """Generate history problems"""
        problems = []
        history_topics = [
            ('wwii', 'When did World War II end?', '1945', 'Include specific dates and key events'),
            ('american_revolution', 'Who was the first US President?', 'George Washington', 'Mention role in revolution and presidency'),
            ('ancient_rome', 'What was the Roman Empire?', 'Ancient civilization that controlled Mediterranean region', 'Include timeline and key achievements'),
            ('industrial_revolution', 'What changed during Industrial Revolution?', 'Shift from agriculture to manufacturing and urbanization', 'Mention technological and social changes'),
            ('cold_war', 'What was the Cold War?', 'Political tension between US and Soviet Union (1947-1991)', 'Include ideological differences')
        ]
        
        for i in range(count):
            topic, question, answer, rubric = random.choice(history_topics)
            score = random.choice(['8/10', '9/10', '7/10', '10/10', '6/10'])
            feedback = f"Good historical knowledge of {topic}. {rubric}. Provide more context."
            
            problems.append({
                'submission': answer,
                'rubric': f"History Question: {question}. {rubric}",
                'score': score,
                'feedback': feedback
            })
        return problems
    
    def generate_literature_problems(self, count: int) -> List[Dict]:
        """Generate literature problems"""
        problems = []
        literature_topics = [
            ('shakespeare', 'Who wrote Romeo and Juliet?', 'William Shakespeare', 'Include time period and other works'),
            ('poetry', 'What is a metaphor?', 'A figure of speech comparing two unlike things directly', 'Provide examples and distinguish from simile'),
            ('novels', 'What is the theme of To Kill a Mockingbird?', 'Racial injustice and moral growth', 'Discuss characters and historical context'),
            ('grammar', 'What is a noun?', 'A word that names a person, place, thing, or idea', 'Include types: proper, common, abstract, concrete'),
            ('writing', 'What makes a good thesis statement?', 'Clear, specific, arguable claim that guides the essay', 'Should be debatable and supportable')
        ]
        
        for i in range(count):
            topic, question, answer, rubric = random.choice(literature_topics)
            score = random.choice(['8/10', '9/10', '7/10', '10/10', '6/10'])
            feedback = f"Good literary analysis of {topic}. {rubric}. Expand with examples."
            
            problems.append({
                'submission': answer,
                'rubric': f"Literature Question: {question}. {rubric}",
                'score': score,
                'feedback': feedback
            })
        return problems
    
    def generate_geography_problems(self, count: int) -> List[Dict]:
        """Generate geography problems"""
        problems = []
        geography_topics = [
            ('capitals', 'What is the capital of France?', 'Paris', 'Include country location and significance'),
            ('continents', 'Name the seven continents', 'Asia, Africa, North America, South America, Antarctica, Europe, Australia', 'List in order of size'),
            ('climate', 'What causes seasons?', 'Earth\'s tilted axis as it orbits the sun', 'Explain axial tilt and orbital mechanics'),
            ('mountains', 'What is the highest mountain?', 'Mount Everest (8,848 meters)', 'Include location and formation process'),
            ('rivers', 'What is the longest river?', 'Nile River (6,650 km)', 'Mention countries it flows through')
        ]
        
        for i in range(count):
            topic, question, answer, rubric = random.choice(geography_topics)
            score = random.choice(['8/10', '9/10', '7/10', '10/10', '6/10'])
            feedback = f"Good geographical knowledge of {topic}. {rubric}. Add more detail."
            
            problems.append({
                'submission': answer,
                'rubric': f"Geography Question: {question}. {rubric}",
                'score': score,
                'feedback': feedback
            })
        return problems
    
    def generate_chemistry_problems(self, count: int) -> List[Dict]:
        """Generate chemistry problems"""
        problems = []
        chemistry_topics = [
            ('periodic_table', 'What is the symbol for gold?', 'Au', 'Include atomic number and properties'),
            ('reactions', 'Balance: H2 + O2 → H2O', '2H2 + O2 → 2H2O', 'Show conservation of mass'),
            ('acids_bases', 'What is pH?', 'Scale measuring hydrogen ion concentration (0-14)', 'Explain acidic, neutral, and basic ranges'),
            ('molecules', 'What is H2O?', 'Water molecule with 2 hydrogen and 1 oxygen atom', 'Describe molecular structure and bonding'),
            ('states', 'Name the three states of matter', 'Solid, liquid, gas', 'Explain molecular behavior in each state')
        ]
        
        for i in range(count):
            topic, question, answer, rubric = random.choice(chemistry_topics)
            score = random.choice(['8/10', '9/10', '7/10', '10/10', '6/10'])
            feedback = f"Good chemistry understanding of {topic}. {rubric}. Show calculations."
            
            problems.append({
                'submission': answer,
                'rubric': f"Chemistry Question: {question}. {rubric}",
                'score': score,
                'feedback': feedback
            })
        return problems
    
    def generate_physics_problems(self, count: int) -> List[Dict]:
        """Generate physics problems"""
        problems = []
        physics_topics = [
            ('motion', 'What is velocity?', 'Rate of change of displacement with time', 'Include direction and units'),
            ('energy', 'What is kinetic energy?', 'Energy of motion: KE = 1/2 mv²', 'Explain relationship to mass and velocity'),
            ('waves', 'What is frequency?', 'Number of wave cycles per second (Hz)', 'Relate to wavelength and wave speed'),
            ('electricity', 'What is current?', 'Flow of electric charge (amperes)', 'Explain relationship to voltage and resistance'),
            ('thermodynamics', 'What is temperature?', 'Measure of average kinetic energy of particles', 'Distinguish from heat and thermal energy')
        ]
        
        for i in range(count):
            topic, question, answer, rubric = random.choice(physics_topics)
            score = random.choice(['8/10', '9/10', '7/10', '10/10', '6/10'])
            feedback = f"Good physics concept of {topic}. {rubric}. Include formulas."
            
            problems.append({
                'submission': answer,
                'rubric': f"Physics Question: {question}. {rubric}",
                'score': score,
                'feedback': feedback
            })
        return problems
    
    def generate_biology_problems(self, count: int) -> List[Dict]:
        """Generate biology problems"""
        problems = []
        biology_topics = [
            ('cells', 'What is a cell?', 'Basic unit of life with membrane, cytoplasm, and genetic material', 'Distinguish prokaryotic and eukaryotic'),
            ('dna', 'What is DNA?', 'Deoxyribonucleic acid containing genetic instructions', 'Explain double helix and base pairs'),
            ('mitosis', 'What is mitosis?', 'Cell division producing two identical diploid cells', 'Include phases and purpose'),
            ('genetics', 'What is a gene?', 'DNA sequence coding for a specific trait', 'Explain alleles and inheritance'),
            ('ecology', 'What is biodiversity?', 'Variety of life forms in an ecosystem', 'Include species, genetic, and ecosystem diversity')
        ]
        
        for i in range(count):
            topic, question, answer, rubric = random.choice(biology_topics)
            score = random.choice(['8/10', '9/10', '7/10', '10/10', '6/10'])
            feedback = f"Good biological understanding of {topic}. {rubric}. Add examples."
            
            problems.append({
                'submission': answer,
                'rubric': f"Biology Question: {question}. {rubric}",
                'score': score,
                'feedback': feedback
            })
        return problems
    
    def generate_english_problems(self, count: int) -> List[Dict]:
        """Generate English language problems"""
        problems = []
        english_topics = [
            ('grammar', 'Identify the verb: "The cat runs quickly"', 'runs', 'Explain action words and their function'),
            ('punctuation', 'When do you use a semicolon?', 'To connect related independent clauses', 'Distinguish from comma and period usage'),
            ('vocabulary', 'What does "ubiquitous" mean?', 'Present everywhere; omnipresent', 'Provide context and synonyms'),
            ('reading', 'What is the main idea?', 'Central point or message of a text', 'Distinguish from supporting details'),
            ('writing', 'What is a topic sentence?', 'First sentence that introduces the paragraph\'s main idea', 'Explain role in paragraph structure')
        ]
        
        for i in range(count):
            topic, question, answer, rubric = random.choice(english_topics)
            score = random.choice(['8/10', '9/10', '7/10', '10/10', '6/10'])
            feedback = f"Good English skills in {topic}. {rubric}. Practice more examples."
            
            problems.append({
                'submission': answer,
                'rubric': f"English Question: {question}. {rubric}",
                'score': score,
                'feedback': feedback
            })
        return problems
    
    def generate_economics_problems(self, count: int) -> List[Dict]:
        """Generate economics problems"""
        problems = []
        economics_topics = [
            ('supply_demand', 'What is supply and demand?', 'Economic model of price determination in a market', 'Explain relationship and equilibrium'),
            ('inflation', 'What is inflation?', 'General increase in prices and fall in purchasing power', 'Include causes and effects'),
            ('gdp', 'What is GDP?', 'Gross Domestic Product - total value of goods and services', 'Explain as economic indicator'),
            ('markets', 'What is a free market?', 'Economic system with minimal government intervention', 'Contrast with planned economy'),
            ('trade', 'What is comparative advantage?', 'Ability to produce at lower opportunity cost', 'Explain benefits of specialization')
        ]
        
        for i in range(count):
            topic, question, answer, rubric = random.choice(economics_topics)
            score = random.choice(['8/10', '9/10', '7/10', '10/10', '6/10'])
            feedback = f"Good economic understanding of {topic}. {rubric}. Use real examples."
            
            problems.append({
                'submission': answer,
                'rubric': f"Economics Question: {question}. {rubric}",
                'score': score,
                'feedback': feedback
            })
        return problems
    
    def generate_training_data(self, total_problems: int, subjects: List[str] = None) -> List[Dict]:
        """Generate training data across multiple subjects"""
        if subjects is None:
            subjects = list(self.subjects.keys())
        
        problems_per_subject = total_problems // len(subjects)
        remaining = total_problems % len(subjects)
        
        all_problems = []
        
        for i, subject in enumerate(subjects):
            count = problems_per_subject + (1 if i < remaining else 0)
            if subject in self.subjects:
                problems = self.subjects[subject](count)
                all_problems.extend(problems)
            else:
                print(f"Warning: Unknown subject '{subject}' skipped")
        
        # Shuffle to mix subjects
        random.shuffle(all_problems)
        return all_problems

def main():
    parser = argparse.ArgumentParser(description='Generate multi-subject training data')
    parser.add_argument('--total', type=int, default=500, help='Total number of problems to generate')
    parser.add_argument('--subjects', nargs='+', help='Subjects to include (default: all)')
    parser.add_argument('--output', default='./dataset/multi_subject_training_data.json', help='Output file path')
    
    args = parser.parse_args()
    
    generator = MultiSubjectDataGenerator()
    
    print(f"Generating {args.total} training examples...")
    if args.subjects:
        print(f"Subjects: {', '.join(args.subjects)}")
    else:
        print(f"Subjects: {', '.join(generator.subjects.keys())}")
    
    training_data = generator.generate_training_data(args.total, args.subjects)
    
    # Save to file
    with open(args.output, 'w') as f:
        json.dump(training_data, f, indent=2)
    
    print(f"\nGenerated {len(training_data)} training examples")
    print(f"Saved to: {args.output}")
    
    # Show subject distribution
    subject_counts = {}
    for problem in training_data:
        subject = problem['rubric'].split(' Question:')[0].replace(' ', '_').lower()
        subject_counts[subject] = subject_counts.get(subject, 0) + 1
    
    print("\nSubject distribution:")
    for subject, count in sorted(subject_counts.items()):
        print(f"  {subject}: {count} examples")
    
    print(f"\nTo train your model, run:")
    print(f"python3 train_model.py --dataset ./dataset --suffix multi_subject_tutor")

if __name__ == '__main__':
    main()