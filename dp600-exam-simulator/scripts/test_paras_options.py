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
    after = content[select_match.end():].strip()
    
    min_pos = 999999
    for starter in EXPLANATION_STARTERS_DP700:
        pos = after.find(starter)
        if pos != -1 and pos < min_pos:
            min_pos = pos
            
    options_raw = after[:min_pos].strip()
    
    # In some questions, like Q29 and Q30, the option has code spanning multiple lines
    # Notice: "This answer is correct." or "This answer is incorrect." is a standalone paragraph or line
    # Let's split options_raw into paragraphs
    raw_paras = [p.strip() for p in re.split(r'\n\s*\n', options_raw) if p.strip()]
    
    opts = []
    for p in raw_paras:
        # Check if p is exactly or starts with "This answer is correct." or "This answer is incorrect."
        if p == 'This answer is correct.' or p.startswith('This answer is correct.'):
            if opts:
                opts[-1]['is_correct'] = True
        elif p == 'This answer is incorrect.' or p.startswith('This answer is incorrect.'):
            if opts:
                opts[-1]['is_correct'] = False
        else:
            opts.append({'text': html.unescape(p), 'is_correct': False})
            
    correct_count = sum(1 for o in opts if o['is_correct'])
    print(f"Q{q_num}: {len(opts)} options, {correct_count} correct")
    if len(opts) < 3 or correct_count == 0:
        print(f"  WARNING for Q{q_num}! Options:")
        for o in opts:
            print("    -", repr(o['text'][:60]), o['is_correct'])
