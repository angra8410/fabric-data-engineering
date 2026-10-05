import re
import html
import json

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

# Let's inspect each question
for idx, (q_num, content) in enumerate(blocks):
    select_match = re.search(r'Select (only one answer|all answers that apply)\.', content)
    prompt = content[:select_match.start()]
    prompt = re.sub(r'^Question \d+[a-z]? of 50\s*', '', prompt).strip()
    prompt = re.sub(r'Practice Assessment for Exam DP-700:[^\n]+\n*', '', prompt).strip()
    
    is_multi = 'all answers' in select_match.group(0)
    after = content[select_match.end():].strip()
    
    # We want to separate the options block from the explanation block.
    # Where does the explanation begin?
    # Notice: the last option line or its "This answer is correct/incorrect" is followed by either:
    # 1) "Objective:"
    # 2) Explanation text explaining the correct answer or why other answers are wrong
    # Let's find where options end.
    
    # Let's check markers or test parsing
