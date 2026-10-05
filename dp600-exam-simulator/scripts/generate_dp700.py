import re
import html
import json

EXPLANATION_STARTERS_DP700 = [
    "Configuring alerts in the Monitor hub is effective",
    "Implementing an incremental load strategy is effective",
    "Using the Monitor hub to filter activities by status",
    "Configuring alerts for future ingestion failures ensures",
    "Setting up alerts for data process delays is crucial",
    "Monitor hub tracks ingestion and transformation activities",
    "Monitoring hub surfaces transformation metrics",
    "Increasing the workspace session timeout prevents",
    "Adding a Fail activity after the Lookup activity is essential",
    "Using traditional Spark engine for queries involving UDFs",
    "Applying V-Order optimizes sorting",
    "Grouping INSERT statements into batches reduces",
    "Setting up an eventstream with Azure Event Hub as a source is essential",
    "Using Microsoft Data Factory pipelines and dataflows are both effective",
    "Using Change Data Capture (CDC) is the most efficient method",
    "Notebooks provide flexible, code-based incremental load patterns",
    "Creating a shortcut in the lakehouse pointing to the cloud storage",
    "Implementing database mirroring in Microsoft Fabric is the most suitable",
    "Type 2 SCD is the most suitable choice",
    "The CREATE TABLE AS SELECT (CTAS) statement is the best choice",
    "The COPY statement with Shared Access Signature efficiently ingests",
    "Azure Synapse Analytics is suitable because it supports all data formats",
    "Using the eventstreams feature in Microsoft Fabric with enhanced capabilities",
    "Implementing Spark Structured Streaming to write data to a Delta table",
    "Delegating tenant-level settings to the domain level allows",
    "Creating a custom Spark pool with autoscaling enabled",
    "Assigning workspaces to specific domains ensures",
    "Creating a custom Spark pool with autoscaling allows for specifying",
    "High concurrency for Spark is controlled via",
    "Using selective deployment is the correct approach",
    "To ensure that only authorized users can edit pipeline settings",
    "Assigning one workspace to all stages undermines",
    "Connecting the workspace to Git enables",
    "In Microsoft Fabric deployment pipelines, assigning a workspace",
    "Column-Level Security is essential for controlling access",
    "Creating an HR role and granting it SELECT permission",
    "The correct answers are to create a security policy",
    "Implementing dynamic data masking on the Email and CreditCardNumber columns",
    "Hard-coding values in the configuration contradicts",
    "Hardcoding dataset paths does not support dynamic execution",
    "Schedule triggers run pipelines on a defined cadence",
    "Objective:"
]

# Domain & Topic metadata for each of the 50 questions
QUESTION_META = {
    1: {"domain": "domain3", "topic": "Monitoring & Alerts", "difficulty": "Medium"},
    2: {"domain": "domain2", "topic": "Data Warehouse Ingestion & CDC", "difficulty": "Medium"},
    3: {"domain": "domain3", "topic": "Monitor Hub Activity Tracking", "difficulty": "Easy"},
    4: {"domain": "domain3", "topic": "Ingestion Monitoring & Alerts", "difficulty": "Medium"},
    5: {"domain": "domain3", "topic": "Performance Bottleneck Troubleshooting", "difficulty": "Medium"},
    6: {"domain": "domain3", "topic": "Monitor Hub for Lakehouse", "difficulty": "Easy"},
    7: {"domain": "domain3", "topic": "Pipeline Transformation Metrics", "difficulty": "Easy"},
    8: {"domain": "domain3", "topic": "Fabric Activator Event Alerts", "difficulty": "Medium"},
    9: {"domain": "domain3", "topic": "Spark Notebook Session Timeouts", "difficulty": "Medium"},
    10: {"domain": "domain1", "topic": "Pipeline Expression & Parameter Typing", "difficulty": "Hard"},
    11: {"domain": "domain1", "topic": "Pipeline JSON Parsing & Dynamic Arrays", "difficulty": "Hard"},
    12: {"domain": "domain3", "topic": "Pipeline Error Handling & Fail Activity", "difficulty": "Medium"},
    13: {"domain": "domain3", "topic": "Spark Optimization & Native Engine UDFs", "difficulty": "Hard"},
    14: {"domain": "domain3", "topic": "Delta Lake Optimization (V-Order & OPTIMIZE)", "difficulty": "Medium"},
    15: {"domain": "domain3", "topic": "Data Warehouse Ingestion Batching", "difficulty": "Medium"},
    16: {"domain": "domain3", "topic": "Delta Lake Auto-Optimize & Compaction", "difficulty": "Hard"},
    17: {"domain": "domain2", "topic": "Eventstreams & Event Processor", "difficulty": "Medium"},
    18: {"domain": "domain2", "topic": "Data Factory Pipelines & Dataflows Gen2", "difficulty": "Medium"},
    19: {"domain": "domain2", "topic": "Change Data Capture (CDC)", "difficulty": "Easy"},
    20: {"domain": "domain2", "topic": "Lakehouse Incremental Loading", "difficulty": "Medium"},
    21: {"domain": "domain2", "topic": "OneLake Shortcuts", "difficulty": "Easy"},
    22: {"domain": "domain2", "topic": "Mirrored Databases", "difficulty": "Medium"},
    23: {"domain": "domain2", "topic": "Slowly Changing Dimensions (SCD Type 2)", "difficulty": "Easy"},
    24: {"domain": "domain2", "topic": "Cross-Database CTAS Queries", "difficulty": "Medium"},
    25: {"domain": "domain2", "topic": "T-SQL COPY Ingestion", "difficulty": "Medium"},
    26: {"domain": "domain2", "topic": "Fabric Storage Architecture Selection", "difficulty": "Medium"},
    27: {"domain": "domain2", "topic": "No-Code Eventstreams", "difficulty": "Easy"},
    28: {"domain": "domain2", "topic": "Spark Structured Streaming", "difficulty": "Hard"},
    29: {"domain": "domain2", "topic": "Kusto Query Language (KQL)", "difficulty": "Hard"},
    30: {"domain": "domain2", "topic": "Stream Windowing & System.Window().Id", "difficulty": "Hard"},
    31: {"domain": "domain1", "topic": "Data Mesh & Domain Governance", "difficulty": "Medium"},
    32: {"domain": "domain3", "topic": "Custom Spark Pools & Autoscaling", "difficulty": "Medium"},
    33: {"domain": "domain1", "topic": "Data Mesh Administration", "difficulty": "Medium"},
    34: {"domain": "domain3", "topic": "Dynamic Executor Allocation", "difficulty": "Medium"},
    35: {"domain": "domain3", "topic": "Spark High Concurrency Settings", "difficulty": "Easy"},
    36: {"domain": "domain1", "topic": "Deployment Pipelines Selective Promotion", "difficulty": "Easy"},
    37: {"domain": "domain1", "topic": "Deployment Pipeline Admin Roles", "difficulty": "Medium"},
    38: {"domain": "domain1", "topic": "Deployment Pipeline Quality Control", "difficulty": "Easy"},
    39: {"domain": "domain1", "topic": "Git Integration & Version Control", "difficulty": "Easy"},
    40: {"domain": "domain1", "topic": "Deployment Pipeline Stage Linking", "difficulty": "Medium"},
    41: {"domain": "domain1", "topic": "Git Revert / Sync Recovery", "difficulty": "Hard"},
    42: {"domain": "domain1", "topic": "Column-Level Security (CLS)", "difficulty": "Easy"},
    43: {"domain": "domain1", "topic": "Column-Level SQL Grant/Deny Roles", "difficulty": "Medium"},
    44: {"domain": "domain1", "topic": "Row-Level Security (RLS) Predicates", "difficulty": "Hard"},
    45: {"domain": "domain1", "topic": "Dynamic Data Masking (DDM)", "difficulty": "Medium"},
    46: {"domain": "domain1", "topic": "Granular SQL Permissions & Compute Access", "difficulty": "Hard"},
    47: {"domain": "domain1", "topic": "Pipeline Dynamic Expressions", "difficulty": "Medium"},
    48: {"domain": "domain1", "topic": "Pipeline Parameters & String Interpolation", "difficulty": "Medium"},
    49: {"domain": "domain1", "topic": "Pipeline Triggers (Schedule)", "difficulty": "Easy"},
    50: {"domain": "domain1", "topic": "Notebook Activity baseParameters Orchestration", "difficulty": "Hard"}
}

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

# Filter out duplicate Question 16 so we have 50 clean questions
filtered_blocks = []
seen_texts = set()
for q_num, content in blocks:
    select_match = re.search(r'Select (only one answer|all answers that apply)\.', content)
    prompt = content[:select_match.start()]
    prompt = re.sub(r'^Question \d+[a-z]? of 50\s*', '', prompt).strip()
    prompt = re.sub(r'Practice Assessment for Exam DP-700:[^\n]+\n*', '', prompt).strip()
    norm_prompt = re.sub(r'\s+', ' ', prompt)
    if norm_prompt in seen_texts:
        print(f"Skipping duplicate: {q_num}")
        continue
    seen_texts.add(norm_prompt)
    filtered_blocks.append((q_num, content, prompt, select_match))

print(f"Total unique questions: {len(filtered_blocks)}")

questions = []
option_letters = ['A', 'B', 'C', 'D', 'E', 'F']

for idx, (raw_q_num, content, prompt, select_match) in enumerate(filtered_blocks):
    q_index = idx + 1
    meta = QUESTION_META[q_index]
    
    is_multi = 'all answers' in select_match.group(0)
    select_count = 1
    if is_multi:
        if 'Which two' in prompt:
            select_count = 2
        elif 'Which three' in prompt:
            select_count = 3
        elif 'Which four' in prompt:
            select_count = 4
        else:
            select_count = 2
            
    after = content[select_match.end():].strip()
    
    min_pos = len(after)
    for starter in EXPLANATION_STARTERS_DP700:
        pos = after.find(starter)
        if pos != -1 and pos < min_pos:
            min_pos = pos
            
    options_raw = after[:min_pos].strip()
    explanation_raw = after[min_pos:].strip()
    
    # Clean HTML entities in prompt and options
    prompt_clean = html.unescape(prompt)
    
    raw_paras = [p.strip() for p in re.split(r'\n\s*\n', options_raw) if p.strip()]
    
    opts = []
    for p in raw_paras:
        if p == 'This answer is correct.' or p.startswith('This answer is correct.'):
            if opts:
                opts[-1]['is_correct'] = True
        elif p == 'This answer is incorrect.' or p.startswith('This answer is incorrect.'):
            if opts:
                opts[-1]['is_correct'] = False
        else:
            clean_opt = html.unescape(p)
            opts.append({'text': clean_opt, 'is_correct': False})
            
    options = []
    correct_ids = []
    for o_idx, o in enumerate(opts):
        letter = option_letters[o_idx]
        options.append({
            "id": letter,
            "text": o['text']
        })
        if o['is_correct']:
            correct_ids.append(letter)
            
    # Extract MS Learn URL if present
    url_match = re.search(r'https?://[^\s\)]+', explanation_raw)
    ms_learn_url = url_match.group(0) if url_match else "https://learn.microsoft.com/en-us/credentials/certifications/fabric-data-engineer-associate/"
    
    # Extract MS Learn Title if present
    title_match = re.search(r'([A-Za-z0-9\s,\-\(\)]+\s*-\s*Training\s*\|\s*Microsoft Learn)', explanation_raw)
    ms_learn_title = title_match.group(1).strip() if title_match else "Implement Data Engineering Solutions Using Microsoft Fabric"
    
    # Clean explanation text
    explanation_clean = html.unescape(explanation_raw)
    
    q_obj = {
        "id": f"dp700-{q_index:02d}",
        "examId": "dp700",
        "type": "multi_select" if is_multi else "multiple_choice",
        "text": prompt_clean,
        "options": options,
        "correctOptionId": correct_ids[0] if correct_ids else "A",
        "correctOptionIds": correct_ids if is_multi else None,
        "selectCount": select_count if is_multi else None,
        "domain": meta["domain"],
        "topic": meta["topic"],
        "difficulty": meta["difficulty"],
        "explanation": explanation_clean,
        "msLearnUrl": ms_learn_url,
        "msLearnTitle": ms_learn_title
    }
    
    questions.append(q_obj)

print(f"Generated {len(questions)} questions")

# Save to JSON
with open('src/data/parsed_dp700_assessment.json', 'w', encoding='utf-8') as f:
    json.dump(questions, f, indent=2, ensure_ascii=False)

# Save to TypeScript
ts_content = '''import { Question } from '../types';

export const DP700_QUESTIONS: Question[] = ''' + json.dumps(questions, indent=2, ensure_ascii=False) + ''';
'''

with open('src/data/dp700Questions.ts', 'w', encoding='utf-8') as f:
    f.write(ts_content)

print("Saved src/data/parsed_dp700_assessment.json and src/data/dp700Questions.ts successfully!")
