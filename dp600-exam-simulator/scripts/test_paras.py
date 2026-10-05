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

results = []

for q_num, content in blocks:
    select_match = re.search(r'Select (only one answer|all answers that apply)\.', content)
    prompt = content[:select_match.start()]
    prompt = re.sub(r'^Question \d+[a-z]? of 50\s*', '', prompt).strip()
    prompt = re.sub(r'Practice Assessment for Exam DP-700:[^\n]+\n*', '', prompt).strip()
    
    is_multi = 'all answers' in select_match.group(0)
    select_count = 1
    if is_multi:
        if 'Which two' in prompt:
            select_count = 2
        elif 'Which three' in prompt:
            select_count = 3
        elif 'Which four' in prompt:
            select_count = 4

    after = content[select_match.end():].strip()
    
    # Split paragraphs by double newline
    paras = [p.strip() for p in re.split(r'\n\s*\n', after) if p.strip()]
    
    # Let's inspect paragraphs
    # In some cases, an option is followed by "This answer is correct." or "This answer is incorrect." in the next paragraph
    # Let's see how paragraphs line up
    print(f"Q{q_num}: {len(paras)} paragraphs")
