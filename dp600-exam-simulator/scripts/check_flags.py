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

print(f"Total blocks found: {len(blocks)}")

# Let's inspect the options for each question
for q_num, content in blocks:
    print(f"=== Q {q_num} ===")
    select_match = re.search(r'Select (only one answer|all answers that apply)\.', content)
    after = content[select_match.end():].strip()
    
    # Check lines
    lines = [l.strip() for l in after.split('\n') if l.strip()]
    correct_lines = [l for l in lines if 'This answer is correct' in l]
    print(f"Correct flags found: {len(correct_lines)}")
