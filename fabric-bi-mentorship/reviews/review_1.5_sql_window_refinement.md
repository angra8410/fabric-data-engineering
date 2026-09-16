# Code Review & Learning Log: Exercise 1.5 (Comparative Window Analytics & Precision Refinement)

- **Date:** 2026-09-15
- **Topic:** Analytical Window Functions (`AVG() OVER (PARTITION BY)`), Precision Control (`ROUND`), Multi-Tier Sorting (`ORDER BY`)
- **Domain:** Credit Union / Loan Portfolio Analytics (`dbo.dimloan` & `dbo.dimmember`)

---

## 1. Business Requirement & Candidate Submission

### 📋 Challenge 1.5 Prompt & Requirements
The business requests a comparative variance analysis:
> *"For each member, compare every individual loan against their personal historical average loan amount, showing the member's average and how much each specific loan deviates (+/-) from that baseline."*

**Specific Output Requirements:**
- Source tables: `dbo.dimloan` and `dbo.dimmember`.
- Columns: `MemberName`, `LoanKey`, `LoanType`, `OriginalAmount`, `member_avg_loan` (rounded to 2 decimal places), `diff_from_avg` (`OriginalAmount - member_avg_loan`).
- Deterministic Ordering: `MemberName ASC`, then `OriginalAmount DESC`.

### Candidate Query
```sql
WITH avg_loans AS ( 
    SELECT 
        dl.MemberKey, 
        dl.LoanType, 
        dl.LoanKey, 
        dl.OriginalAmount, 
        -- Calculate individual member average and round to 2 decimals
        ROUND(AVG(dl.OriginalAmount) OVER (PARTITION BY dl.MemberKey), 2) AS member_avg_loan 
    FROM dimloan dl 
)
SELECT 
    dm.MemberName,
    al.LoanKey,
    al.LoanType,
    al.OriginalAmount,
    al.member_avg_loan,
    -- Calculate difference from the rounded average
    (al.OriginalAmount - al.member_avg_loan) AS diff_from_avg
FROM avg_loans al 
INNER JOIN dimmember dm ON al.MemberKey = dm.MemberKey
-- Strict sorting order requested by the prompt
ORDER BY dm.MemberName ASC, al.OriginalAmount DESC;
```

---

## 2. Senior PR Review Analysis

### ✅ Strengths & Level-Up Highlights
1. **Accurate Window Specification Without `ORDER BY` Inside `OVER()`:**
   - Unlike ranking (`ROW_NUMBER()`, `RANK()`) or cumulative running totals where an inner `ORDER BY` creates a dynamic frame, computing an overall partition average requires an unbounded frame across the entire member partition: `OVER (PARTITION BY dl.MemberKey)`.
2. **Elimination of Floating-Point Drift:**
   - Wrapping `AVG(dl.OriginalAmount)` in `ROUND(..., 2)` inside the CTE resolves the raw IEEE repeating decimal noise observed in Exercise 1.4 (e.g. `19007.746666666667`).
3. **Deterministic Multi-Tier Sort:**
   - `ORDER BY dm.MemberName ASC, al.OriginalAmount DESC` guarantees that:
     - All loans for a single member are grouped together alphabetically.
     - Within each member's portfolio, their highest-exposure loans appear at the top.

---

### 🛑 Areas for Production Optimization

#### 1. Schema Qualification (`dbo.`)
- While the CTE specifies `FROM dimloan dl`, standard enterprise SQL guidelines require explicit schema namespaces (`FROM dbo.dimloan dl`). Omitting the schema can force the query parser to check user-default schemas before resolving `dbo`, incurring parse overhead.

#### 2. Sub-Penny Rounding on Subtraction (`diff_from_avg`)
- Depending on the engine data type of `OriginalAmount` (e.g., `FLOAT` vs. `DECIMAL(18, 2)` / `MONEY`), computing `(al.OriginalAmount - al.member_avg_loan)` can occasionally reintroduce binary floating-point representation anomalies (e.g., `0.000000000000004`).
- **Production Best Practice:** Explicitly wrap the difference calculation or cast to `DECIMAL(18, 2)` / `ROUND(..., 2)`:
  ```sql
  ROUND(al.OriginalAmount - al.member_avg_loan, 2) AS diff_from_avg
  ```

#### 3. Architectural Pattern: CTE vs. Single Pass
- The CTE pattern used is clean, maintainable, and readable.
- If preferred for pipeline brevity or view creation, this can also be expressed directly by joining `dbo.dimmember` and `dbo.dimloan` in the inner CTE or evaluating the window function in a derived table.

---

## 3. Approved Production Solution
```sql
WITH member_loan_metrics AS ( 
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
    m.LoanKey,
    m.LoanType,
    m.OriginalAmount,
    m.member_avg_loan,
    ROUND(m.OriginalAmount - m.member_avg_loan, 2) AS diff_from_avg
FROM member_loan_metrics m 
INNER JOIN dbo.dimmember dm 
    ON m.MemberKey = dm.MemberKey
ORDER BY 
    dm.MemberName ASC, 
    m.OriginalAmount DESC;
```
