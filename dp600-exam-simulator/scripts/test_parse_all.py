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

for q_num, content in blocks:
    # 1. Check prompt part
    select_match = re.search(r'Select (only one answer|all answers that apply)\.', content)
    if not select_match:
        print(f"FAILED select match on Q{q_num}")
        continue
    
    prompt = content[:select_match.start()]
    prompt = re.sub(r'^Question \d+[a-z]? of 50\s*', '', prompt).strip()
    # clean any assessment header from prompt
    prompt = re.sub(r'Practice Assessment for Exam DP-700:[^\n]+\n*', '', prompt).strip()

    remainder = content[select_match.end():].strip()
    
    # Let's see what is inside remainder
    # Check if we can identify where options end and explanation begins
    print(f"Q{q_num}: type={'multi' if 'all answers' in select_match.group(0) else 'single'}, prompt len={len(prompt)}")
