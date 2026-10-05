import re
import html
import json

with open('src/data/raw_dp700_assessment.txt', 'r', encoding='utf-8') as f:
    raw = f.read().replace('\r\n', '\n')

# Find all blocks: Question (\d+[a-z]?) of 50
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
