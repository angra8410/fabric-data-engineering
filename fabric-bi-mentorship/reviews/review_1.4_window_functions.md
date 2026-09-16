# Code Review & Learning Log: Exercise 1.4 (Window Functions & Partitioning)

- **Date:** 2026-09-15
- **Topic:** Window Functions (`AVG() OVER (PARTITION BY)`), Granularity Preservation vs. `GROUP BY`, CTE Structuring
- **Domain:** Credit Union / Loan Portfolio Analytics (`dbo.dimloan` & `dbo.dimmember`)

---

## 1. Candidate Submission
```sql
WITH avg_loans AS ( 
    SELECT 
        dl.MemberKey, 
        dl.LoanType, 
        dl.LoanKey, 
        dl.OriginalAmount, 
        avg(dl.OriginalAmount) OVER (PARTITION BY dl.MemberKey) as member_avg_loan 
    FROM dimloan dl 
)
SELECT 
    dm.MemberName,
    al.LoanKey,
    al.LoanType,
    al.OriginalAmount,
    al.member_avg_loan as member_avg_loan,
    (al.OriginalAmount - al.member_avg_loan) AS diff_from_avg
FROM avg_loans al 
INNER JOIN dimmember dm ON al.MemberKey=dm.MemberKey;
```

---

## 2. Senior PR Review Analysis

### ✅ Positive Architectural Takeaways
1. **Granularity Preservation (Window Function vs. `GROUP BY`):**
   - Candidate correctly identified that a classical `GROUP BY dl.MemberKey` would collapse individual loans into a single aggregated row per member, losing `LoanKey`, `LoanType`, and individual `OriginalAmount` details.
   - Using `AVG(dl.OriginalAmount) OVER (PARTITION BY dl.MemberKey)` elegantly calculates partition-level metrics while broadcasting them across every individual transaction row.
2. **CTE for Column Alias Reuse:**
   - In SQL, you cannot reference a newly computed window alias (`member_avg_loan`) in the same `SELECT` clause to compute `diff_from_avg`. Staging the window function inside a CTE (`avg_loans`) avoids duplicating the window definition expression `(al.OriginalAmount - AVG(dl.OriginalAmount) OVER (...))`.

---

### 🛑 Issues Identified

#### 1. Floating-Point Precision Leakage (Unrounded Averages)
- **Observed Result:** Values like `19007.746666666667` and `-14044.976666666667` appear in the output.
- **The Financial Impact:** In reporting and financial reconciliation, arbitrary floating-point repeating decimals look unprofessional on dashboards and can cause sub-penny rounding drift across BI downstream layers.
- **Fix:** Explicitly round financial averages to 2 decimal places:
  ```sql
  ROUND(AVG(dl.OriginalAmount) OVER (PARTITION BY dl.MemberKey), 2) AS member_avg_loan
  ```

#### 2. Lack of Deterministic Ordering (`ORDER BY`)
- **Risk:** SQL tables and intermediate sets are unordered by definition. Without an explicit `ORDER BY` in the outer query, the storage engine / distributed MPP query optimizer (such as Fabric SQL / Synapse) returns rows in arbitrary order based on worker thread scheduling.
- **Fix:** Always provide deterministic sorting when presenting analytical comparisons (e.g., `ORDER BY dm.MemberName ASC, al.OriginalAmount DESC`).

#### 3. Schema Qualification & Alias Hygiene
- Always qualify tables with their schema (`dbo.dimloan`, `dbo.dimmember`) to prevent schema-search path overhead and avoid ambiguous object resolution.
- Redundant alias clause: `al.member_avg_loan as member_avg_loan` is unnecessary syntax noise.

---

## 3. Approved Production Solution
```sql
WITH avg_loans AS ( 
    SELECT 
        dl.MemberKey, 
        dl.LoanKey, 
        dl.LoanType, 
        dl.OriginalAmount, 
        ROUND(AVG(dl.OriginalAmount) OVER (PARTITION BY dl.MemberKey), 2) AS member_avg_loan 
    FROM dbo.dimloan dl 
)
SELECT 
    dm.MemberName,
    al.LoanKey,
    al.LoanType,
    al.OriginalAmount,
    al.member_avg_loan,
    ROUND(al.OriginalAmount - al.member_avg_loan, 2) AS diff_from_avg
FROM avg_loans al 
INNER JOIN dbo.dimmember dm 
    ON al.MemberKey = dm.MemberKey
ORDER BY 
    dm.MemberName ASC, 
    al.OriginalAmount DESC;
```
