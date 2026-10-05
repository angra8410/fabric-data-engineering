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

print(f"Loaded {len(blocks)} blocks")

def extract_options(after_text, min_pos):
    options_raw = after_text[:min_pos].strip()
    # Replace HTML entities
    options_raw = html.unescape(options_raw)
    
    # We want to extract options and identify which ones have "This answer is correct"
    # An option can be followed by "This answer is correct." or "This answer is incorrect."
    # Let's split on options
    # In almost all questions, options are separated by double newlines or lines
    lines = [l.strip() for l in options_raw.split('\n') if l.strip()]
    
    options = []
    current_text = []
    is_correct = False
    
    for line in lines:
        if line == 'This answer is correct.':
            is_correct = True
        elif line == 'This answer is incorrect.':
            pass
        else:
            # If line is not a flag, could it be part of previous option or a new option?
            # If previous option finished (it had a flag, or we were empty):
            if is_correct:
                # previous option ended
                if current_text:
                    options.append(('\n'.join(current_text), True))
                    current_text = []
                    is_correct = False
            current_text.append(line)
            
    if current_text:
        options.append(('\n'.join(current_text), is_correct))
        
    return options

# Let's test this logic on all blocks
for q_num, content in blocks:
    select_match = re.search(r'Select (only one answer|all answers that apply)\.', content)
    after = content[select_match.end():].strip()
    
    min_pos = 999999
    for starter in EXPLANATION_STARTERS_DP700:
        pos = after.find(starter)
        if pos != -1 and pos < min_pos:
            min_pos = pos
            
    opts = extract_options(after, min_pos)
    correct_count = sum(1 for _, c in opts if c)
    print(f"Q{q_num}: {len(opts)} options, {correct_count} correct")
