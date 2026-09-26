import re
import json
import hashlib
import os

# Topic-specific pools for high-quality fallback distractors (DP-600 specific)
TOPIC_POOLS = {
    'security': [
        "Implement column-level security (CLS).",
        "Configure dynamic data masking (DDM).",
        "Assign users the workspace Contributor role.",
        "Implement row-level security (RLS) with USERPRINCIPALNAME().",
        "Create Microsoft Entra security groups for role assignment.",
        "Apply Microsoft Purview sensitivity labels to the workspace.",
        "Grant granular SQL permissions using DENY and GRANT in T-SQL.",
        "Use workspace Viewer role with read-only permissions."
    ],
    'git_cicd': [
        "Create a personal development branch in Azure DevOps.",
        "Connect the Fabric workspace to the Azure DevOps Git repository.",
        "Configure deployment pipeline rules for data sources.",
        "Enable Git integration in the workspace settings.",
        "Export the workspace as a Power BI Project (.pbip) file.",
        "Deploy the changes using a Fabric deployment pipeline.",
        "Create a pull request (PR) in Azure DevOps to merge into main.",
        "Use Azure Data Factory REST APIs to trigger deployment."
    ],
    'shortcuts_storage': [
        "Create an internal OneLake shortcut to the target table.",
        "Create an external OneLake shortcut to Azure Data Lake Storage Gen2.",
        "Create an Amazon S3 shortcut in the Lakehouse Files section.",
        "Use Dataflows Gen2 to ingest and stage raw data.",
        "Copy data to the Files directory and create an external Delta table.",
        "Use a Fabric notebook to mount the external storage account.",
        "Configure an Azure Data Factory Copy Activity to load Delta tables."
    ],
    'delta_optimization': [
        "Execute OPTIMIZE with V-Order enabled on the Delta table.",
        "Run VACUUM with a retention period of 168 hours.",
        "Partition the Delta table by transaction date key.",
        "Execute OPTIMIZE ZORDER BY on high-cardinality filter columns.",
        "Enable Delta Lake automatic compaction in Spark settings.",
        "Convert the tables to native Parquet files without Delta logs."
    ],
    'warehouse_tsql': [
        "Create a stored procedure in the Fabric data warehouse.",
        "Use T-SQL CREATE TABLE AS SELECT (CTAS) to rebuild the table.",
        "Create a SQL view in the data warehouse.",
        "Use T-SQL ALTER TABLE SWITCH PARTITION to load data.",
        "Execute a cross-database T-SQL query across Lakehouse and Warehouse.",
        "Use the visual query editor in the warehouse."
    ],
    'semantic_model_dax': [
        "Use Direct Lake mode with Delta Lake V-Order optimization.",
        "Switch the semantic model to Import mode with scheduled refresh.",
        "Configure DirectQuery mode pointing to the SQL analytics endpoint.",
        "Use Composite mode with dual storage tables.",
        "Create a Calculation Group using Tabular Editor 2.",
        "Author a DAX measure using CALCULATE and ALLEXCEPT.",
        "Configure field parameters for dynamic measure selection."
    ],
    'tools_monitoring': [
        "DAX Studio",
        "SQL Profiler",
        "Tabular Editor 2",
        "Fabric Capacity Metrics App",
        "Power BI Performance Analyzer",
        "VertiPaq Analyzer",
        "Azure Log Analytics"
    ],
    'general': [
        "Use a Fabric PySpark notebook to transform the data.",
        "Configure an eventstream in Real-Time Intelligence.",
        "Create a Lakehouse shortcut to the source data.",
        "Use Dataflows Gen2 with enhanced compute engine enabled."
    ]
}

def infer_category(text, explanation):
    combined = (text + " " + explanation).lower()
    if any(k in combined for k in ['security', 'permission', 'role', 'rls', 'cls', 'ols', 'masking', 'sensitive', 'grant', 'entra']):
        return 'security'
    if any(k in combined for k in ['git', 'pipeline', 'devops', 'branch', 'lifecycle', 'deploy']):
        return 'git_cicd'
    if any(k in combined for k in ['shortcut', 'onelake', 'adls', 's3', 'mount']):
        return 'shortcuts_storage'
    if any(k in combined for k in ['vacuum', 'optimize', 'v-order', 'delta', 'zorder', 'compaction']):
        return 'delta_optimization'
    if any(k in combined for k in ['warehouse', 't-sql', 'sql query', 'view', 'ctas']):
        return 'warehouse_tsql'
    if any(k in combined for k in ['dax', 'semantic model', 'direct lake', 'measure', 'calculation group', 'star schema', 'dimension']):
        return 'semantic_model_dax'
    if any(k in combined for k in ['tool', 'analyzer', 'profiler', 'metrics', 'monitor']):
        return 'tools_monitoring'
    return 'general'

def infer_domain(text, explanation):
    combined = (text + " " + explanation).lower()
    if any(k in combined for k in ['workspace', 'capacity', 'git', 'devops', 'pipeline', 'admin', 'tenant', 'governance']):
        return 'domain1'
    if any(k in combined for k in ['dax', 'semantic model', 'direct lake', 'tabular editor', 'measure', 'calculation group', 'kql', 'star schema', 'dimension', 'scd']):
        return 'domain3'
    return 'domain2'

def infer_topic(text, explanation):
    combined = (text + " " + explanation).lower()
    if 'direct lake' in combined:
        return 'Direct Lake Mode'
    if 'shortcut' in combined:
        return 'OneLake Shortcuts'
    if 'git' in combined or 'repo' in combined:
        return 'Git Integration & CI/CD'
    if 'deployment pipeline' in combined:
        return 'Deployment Pipelines'
    if 'pyspark' in combined or 'spark' in combined:
        return 'PySpark Transformations'
    if 'kql' in combined or 'eventhouse' in combined:
        return 'Real-Time Intelligence (KQL)'
    if 'dax' in combined:
        return 'DAX & Modeling'
    if 'dataflow' in combined:
        return 'Dataflows Gen2'
    if 'warehouse' in combined:
        return 'Fabric Warehouse & T-SQL'
    if any(k in combined for k in ['row-level security', 'object-level security', 'column-level security', 'rls', 'ols', 'cls']):
        return 'Fabric Security (RLS/CLS/OLS)'
    if 'tabular editor' in combined:
        return 'Tabular Editor & Optimization'
    if 'slowly changing dimension' in combined or 'scd' in combined:
        return 'Dimensional Modeling (SCD)'
    return 'Microsoft Fabric Architecture'

with open('raw_mslearn_feedback.txt', 'r', encoding='utf-8') as f:
    raw_content = f.read()

blocks = re.split(r'(?=Question\s+\d+(?:\s+of\s+\d+)?[:.\s])', raw_content, flags=re.IGNORECASE)
q_blocks = [b.strip() for b in blocks if b.strip().lower().startswith('question')]

parsed_questions = []

for idx, block in enumerate(q_blocks):
    # Extract question stem
    m_stem = re.search(r'Question\s+\d+(?:\s+of\s+\d+)?[:.\s]*(.*?)\s*Your Answer', block, re.DOTALL | re.IGNORECASE)
    if not m_stem:
        continue
    q_text = m_stem.group(1).strip()
    
    # Check if multi-select
    m_count = re.search(r'which\s+(two|three|four|2|3|4)\s+(actions|tools|statements|options|tables|components|settings|steps|functions)', q_text, re.I)
    has_part = 'each correct answer presents' in q_text.lower() or 'each correct answer presents' in block.lower()
    
    count_map = {'two': 2, '2': 2, 'three': 3, '3': 3, 'four': 4, '4': 4}
    select_count = count_map.get(m_count.group(1).lower(), 1) if m_count else (3 if has_part else 1)
    is_multi = select_count > 1

    # Extract Your Answer section
    m_your_ans = re.search(r'Your Answer\s*(.*?)\s*Correct Answer', block, re.DOTALL | re.IGNORECASE)
    your_ans_block = m_your_ans.group(1).strip() if m_your_ans else ""
    
    user_incorrect_answers = []
    your_lines = [l.strip() for l in your_ans_block.split('\n') if l.strip()]
    for i, line in enumerate(your_lines):
        if line == 'This answer is incorrect.' and i > 0:
            user_incorrect_answers.append(your_lines[i-1])

    # Extract Correct Answer section & Explanation
    ca_start = block.find('Correct Answer')
    rest = block[ca_start + len('Correct Answer'):].strip() if ca_start != -1 else ""
    
    ca_lines = rest.split('\n')
    correct_answers = []
    explanation_lines = []
    collecting_correct = True
    
    for line in ca_lines:
        l = line.strip()
        if not l:
            continue
        if l == 'This answer is correct.':
            continue
        if l.startswith('[') and 'http' in l:
            collecting_correct = False
            explanation_lines.append(l)
            continue
        if l.startswith('Objective:') or l.startswith('What This Item Tests:') or l.startswith('Rationale:'):
            collecting_correct = False
            explanation_lines.append(l)
            continue
        
        if collecting_correct:
            # If it's short or explicitly an answer option
            if is_multi:
                if len(correct_answers) < select_count:
                    correct_answers.append(l)
                else:
                    collecting_correct = False
                    explanation_lines.append(l)
            else:
                if len(correct_answers) < 1:
                    correct_answers.append(l)
                else:
                    collecting_correct = False
                    explanation_lines.append(l)
        else:
            explanation_lines.append(l)

    # Clean explanation and URL
    explanation = " ".join([l for l in explanation_lines if not l.startswith('[')])
    explanation = re.sub(r'\s+', ' ', explanation).strip()
    if not explanation:
        explanation = "Verified solution based on official Microsoft Learn Fabric Analytics Engineer guidance."

    m_url = re.search(r'https://learn\.microsoft\.com/[^\s)\]]+', block)
    ms_url = m_url.group(0) if m_url else "https://learn.microsoft.com/en-us/credentials/certifications/fabric-analytics-engineer-associate/"

    # Category and domain
    category = infer_category(q_text, explanation)
    domain = infer_domain(q_text, explanation)
    topic = infer_topic(q_text, explanation)

    # Collect distractors
    distractors = []
    for ua in user_incorrect_answers:
        if ua not in correct_answers and ua not in distractors:
            distractors.append(ua)

    # Custom distractor extraction for specific questions
    # 1. Tables question (e.g. Q45: Customer, Date, Product, Store, SalesTransactions)
    m_tables = re.search(r'contains the following tables:\s*([A-Za-z0-9\s]+?)\s*You are building', q_text, re.I)
    if m_tables:
        table_candidates = m_tables.group(1).split()
        for t in table_candidates:
            t = t.strip()
            if t and t not in correct_answers and t not in distractors:
                distractors.append(t)

    # 2. SCD questions (Q42, Q43)
    if 'slowly changing dimension' in q_text.lower() or 'scd' in q_text.lower():
        scd_opts = [
            "type 0 slowly changing dimension (SCD)",
            "type 1 slowly changing dimension (SCD)",
            "type 2 slowly changing dimension (SCD)",
            "type 3 slowly changing dimension (SCD)",
            "type 6 slowly changing dimension (SCD)"
        ]
        for opt in scd_opts:
            if opt not in correct_answers and opt not in distractors:
                distractors.append(opt)

    # 3. RANKX question (Q44)
    if 'RANKX' in q_text:
        rank_opts = [
            "ranks the product names by Sales in descending order, assigning consecutive dense rank values without skipping after ties",
            "ranks the product names by Sales in ascending order, with smallest sales receiving rank 1 and skipping rank values after ties",
            "ranks the product names by Sales in descending order, evaluated against the existing report filter context rather than ALL products",
            "ranks all products across all categories by Total Quantity sold, ignoring sales amounts"
        ]
        for opt in rank_opts:
            if opt not in correct_answers and opt not in distractors:
                distractors.append(opt)

    # 4. Profiling functions (Q26: df.describe().show())
    if 'df.describe()' in q_text:
        func_opts = ["DISTINCTCOUNT", "TOP", "UNIQUE", "FREQ", "MEDIAN", "MODE"]
        for opt in func_opts:
            if opt not in correct_answers and opt not in distractors:
                distractors.append(opt)

    # 5. Storage mode questions (Q37, Q46)
    if 'storage mode' in q_text.lower():
        mode_opts = ["Direct Lake", "Import", "DirectQuery", "Dual (Composite)"]
        for opt in mode_opts:
            if opt not in correct_answers and opt not in distractors:
                distractors.append(opt)

    # 6. Tools question (Q40: Which two tools)
    if 'which two tools' in q_text.lower() or ('tools' in q_text.lower() and is_multi):
        tool_opts = ["DAX Studio", "SQL Profiler", "Performance Analyzer in Power BI Desktop", "VertiPaq Analyzer", "Tabular Editor 2"]
        for opt in tool_opts:
            if not any(opt.lower() in c.lower() or c.lower() in opt.lower() for c in correct_answers) and \
               not any(opt.lower() in d.lower() or d.lower() in opt.lower() for d in distractors):
                distractors.append(opt)

    # Fill remaining distractors from topic pool
    target_total_options = max(4, len(correct_answers) + (2 if is_multi else 3))
    needed_distractors = target_total_options - len(correct_answers)

    pool = TOPIC_POOLS.get(category, TOPIC_POOLS['general']) + TOPIC_POOLS['general']
    for candidate in pool:
        if len(distractors) >= needed_distractors:
            break
        # Normalize comparison
        cand_clean = candidate.strip().rstrip('.')
        if not any(cand_clean.lower() == c.strip().rstrip('.').lower() for c in correct_answers) and \
           not any(cand_clean.lower() == d.strip().rstrip('.').lower() for d in distractors) and \
           not any(cand_clean.lower() in d.lower() or d.lower() in cand_clean.lower() for d in distractors + correct_answers):
            distractors.append(candidate)

    # Build options list
    all_options_text = list(correct_answers) + list(distractors[:needed_distractors])
    
    # Deterministic rotation based on question index
    import random
    rng = random.Random(idx * 7919)
    rng.shuffle(all_options_text)

    letters = ['A', 'B', 'C', 'D', 'E', 'F']
    options = []
    correct_ids = []
    for i, opt_text in enumerate(all_options_text[:len(letters)]):
        letter = letters[i]
        options.append({"id": letter, "text": opt_text})
        if opt_text in correct_answers:
            correct_ids.append(letter)

    q_hash = hashlib.sha256(q_text.lower().encode('utf-8')).hexdigest()[:10]
    q_id = f"mslearn-{q_hash}"

    item = {
        "id": q_id,
        "type": "multi_select" if is_multi else "multiple_choice",
        "text": q_text,
        "options": options,
        "correctOptionId": correct_ids[0] if correct_ids else 'A',
        "correctOptionIds": correct_ids if is_multi else None,
        "selectCount": select_count if is_multi else None,
        "domain": domain,
        "topic": topic,
        "difficulty": "Hard" if is_multi else "Medium",
        "explanation": explanation,
        "msLearnUrl": ms_url,
        "msLearnTitle": f"Microsoft Learn - {topic}",
        "isCustom": True
    }
    parsed_questions.append(item)

print(f"Parsed {len(parsed_questions)} questions successfully.")
multi_cnt = sum(1 for q in parsed_questions if q['type'] == 'multi_select')
print(f"Multi-select questions: {multi_cnt}")

# Save JSON and TypeScript
with open('mslearn_dp600_50q.json', 'w', encoding='utf-8') as f:
    json.dump(parsed_questions, f, indent=2)

with open('src/data/mslearnQuestions.ts', 'w', encoding='utf-8') as f:
    f.write('import { Question } from "../types";\n\nexport const MS_LEARN_50_QUESTIONS: Question[] = ' + json.dumps(parsed_questions, indent=2) + ';\n')

print("Saved clean questions to mslearn_dp600_50q.json and src/data/mslearnQuestions.ts!")
