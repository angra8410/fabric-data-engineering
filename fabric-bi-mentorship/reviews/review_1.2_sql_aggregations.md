# Code Review & Learning Log: Exercise 1.2 (Aggregations, Grouping & SQL Logic)

- **Date:** 2026-09-12
- **Topic:** Logical Order of Execution, Aggregates (`SUM`, `AVG`, `COUNT`), `HAVING` vs. `WHERE`, and Precision Control (`ROUND`)
- **Domain:** Credit Union / Loan Portfolio Analytics (`dbo.dimloan` & `dbo.dimbranch`)

---

## 1. Candidate Submission
```sql
SELECT 
    b.BranchName,
    l.LoanType,
    count(l.LoanType) AS total_loans,
    sum(round(l.OriginalAmount)) AS total_originated_amount,
    avg(round(l.InterestRate)) AS avg_interest_rate,
    max(l.OriginalAmount) AS max_loan_amount
FROM dimloan l
LEFT JOIN dimbranch b ON l.BranchID=b.BranchID
WHERE l.StartDate >= '2024-01-01'
GROUP BY b.BranchName, l.LoanType
HAVING SUM(total_originated_amount) > 50000
ORDER BY total_originated_amount DESC;
```

---

## 2. Senior PR Review Analysis

### 🛑 Issue 1: The Logical Order of Execution Trap (`HAVING SUM(alias)`)
- **Error:** In SQL, the query is not evaluated in the written order (`SELECT` $\rightarrow$ `FROM` $\rightarrow$ `WHERE`).
- **The Actual Order of Execution:**
  1. `FROM` & `JOIN` (Build the joined dataset)
  2. `WHERE` (Filter base rows before grouping)
  3. `GROUP BY` (Bucket rows into groups)
  4. `HAVING` (Filter the resulting groups)  <-- **Evaluated HERE**
  5. `SELECT` (Compute expressions and assign aliases) <-- **Alias created HERE**
  6. `ORDER BY` (Sort final output)
- **The Breakdown:**
  When step 4 (`HAVING`) runs, step 5 (`SELECT`) has **not happened yet**. The alias `total_originated_amount` does not exist in scope. Writing `HAVING SUM(total_originated_amount)` attempts to take the sum of an alias that doesn't exist, and attempts to aggregate an already aggregated value.
- **Fix:** In `HAVING`, repeat the raw aggregate expression:
  ```sql
  HAVING SUM(l.OriginalAmount) > 50000
  ```

---

### 🛑 Issue 2: Mathematical Precision: Aggregate First, Round Second
- **Candidate Code:**
  ```sql
  avg(round(l.InterestRate)) AS avg_interest_rate
  ```
- **The Financial Disaster:**
  Interest rates are small decimals (e.g., `0.0825` for 8.25%).
  In T-SQL / Fabric SQL, `ROUND(0.0825)` without specifying decimals rounds to 0 decimals, turning `0.0825` into `0.0`.
  Therefore, `AVG(ROUND(0.0825))` calculates `AVG(0.0) = 0.0000`.
- **Golden Analytical Rule:**
  **Never round row-level inputs before aggregating.** Doing so distorts totals and causes rounding error drift.
  **Always aggregate the full precision first, then round the aggregate:**
  ```sql
  ROUND(SUM(l.OriginalAmount), 2) AS total_originated_amount,
  ROUND(AVG(l.InterestRate), 4)   AS avg_interest_rate
  ```

---

### 💡 Issue 3: `COUNT(column)` vs. `COUNT(*)`
- `COUNT(l.LoanType)` skips rows where `LoanType IS NULL`.
- If your goal is to count how many loans were issued in that category, `COUNT(*)` communicates analytical intent: "Count the number of loan records in this group."

---

## 3. Approved Production Solution
```sql
SELECT 
    COALESCE(b.BranchName, 'Unknown Branch') AS branch_name,
    l.LoanType                               AS loan_type,
    COUNT(*)                                 AS total_loans,
    ROUND(SUM(l.OriginalAmount), 2)          AS total_originated_amount,
    ROUND(AVG(l.InterestRate), 4)            AS avg_interest_rate,
    MAX(l.OriginalAmount)                    AS max_loan_amount
FROM dbo.dimloan l
LEFT JOIN dbo.dimbranch b 
    ON l.BranchID = b.BranchID
WHERE l.StartDate >= '2024-01-01'
GROUP BY 
    b.BranchName, 
    l.LoanType
HAVING SUM(l.OriginalAmount) > 50000
ORDER BY total_originated_amount DESC;
```
