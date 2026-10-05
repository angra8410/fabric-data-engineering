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

print(f"Loaded {len(blocks)} blocks")

def parse_block(q_num, content):
    select_match = re.search(r'Select (only one answer|all answers that apply)\.', content)
    prompt = content[:select_match.start()]
    prompt = re.sub(r'^Question \d+[a-z]? of 50\s*', '', prompt).strip()
    prompt = re.sub(r'Practice Assessment for Exam DP-700:[^\n]+\n*', '', prompt).strip()
    is_multi = 'all answers' in select_match.group(0)

    after = content[select_match.end():].strip()
    
    # In 'after', let's find occurrences of "This answer is correct." or "This answer is incorrect."
    # The last option is often immediately followed by "This answer is correct." or "This answer is incorrect."
    # AND optionally an explanation paragraph.
    # If the last option is not marked with correct/incorrect, the explanation starts after it.
    
    return {
        "q_num": q_num,
        "prompt": prompt,
        "is_multi": is_multi,
        "after": after
    }

parsed = [parse_block(q_num, content) for q_num, content in blocks]
print("All parsed basic structure")
