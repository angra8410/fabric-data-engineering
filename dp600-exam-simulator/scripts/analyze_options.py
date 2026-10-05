import re
import html

with open('src/data/raw_dp700_assessment.txt', 'r', encoding='utf-8') as f:
    raw = f.read().replace('\r\n', '\n')

pattern = r'Question (\d+[a-z]?) of 50'
matches = list(re.finditer(pattern, raw))

blocks = []
for i in range(len(matches)):
    start = matches[i].start()
    end = matches[i+1].start() if i + 1 < len(matches) else len(raw)
    q_num = matches[i].group(1)
    content = raw[start:end]
    blocks.append((q_num, content))

for q_num, content in blocks:
    select_match = re.search(r'Select (only one answer|all answers that apply)\.', content)
    remainder = content[select_match.end():].strip()
    
    # Split remainder by double newlines or lines
    # Let's inspect what lines exist
    lines = [l.strip() for l in remainder.split('\n') if l.strip()]
    
    # Let's check where the explanation might start.
    # In MS Learn assessments:
    # Options are either plain text, or followed by "This answer is correct." or "This answer is incorrect."
    # The explanation is either:
    # 1. A paragraph starting with "Objective:"
    # 2. Or a paragraph explaining the answer, often containing words like:
    #    "is effective because", "Setting up alerts", "The correct answer", "Using ", "Implementing ", etc.
    # Let's print out what follows the last option for each question.
