# Code Review & Learning Log: Exercise 1.3 (CTEs & Credit Risk Exposure)

- **Date:** 2026-09-13
- **Topic:** Common Table Expressions (CTEs), Pre-aggregation Performance ("Lean CTE"), Granularity Control, and Dimension Joins
- **Domain:** Credit Union / Loan Portfolio Analytics (`dbo.dimloan` & `dbo.dimmember`)

---

## 1. Candidate Submission
```sql
WITH loans_preaggregated AS (
    SELECT 
        m.MemberKey,
        m.MemberName,
        m.CreditScore,
        m.DebtToIncomeRatio,
        count(l.LoanType) AS active_loan_count,
        round(sum(l.OriginalAmount), 2) AS totalamount   
    FROM dimmember m 
    INNER JOIN dimloan l 
        ON m.MemberKey = l.MemberKey
    WHERE m.MemberKey > 1 
    GROUP BY 
        m.MemberKey, 
        m.MemberName, 
        m.CreditScore, 
        m.DebtToIncomeRatio
    HAVING sum(l.OriginalAmount) > 30000 
       AND count(l.LoanType) > 1
)
SELECT 
    lp.MemberKey,
    lp.MemberName,
    lp.CreditScore,
    lp.DebtToIncomeRatio,
    lp.active_loan_count,
    lp.totalamount
FROM loans_preaggregated lp
ORDER BY lp.totalamount DESC;
```

---

## 2. Senior PR Review Analysis

### 🛑 Architectural Point: Joining Before Grouping vs. The "Lean CTE" Pattern
- **What Happened:** In the submission, `dimmember` was joined to `dimloan` *inside* the CTE before the `GROUP BY`.
- **The Engine Overhead:**
  - When joining dimensions before grouping, the database engine must carry wide textual columns (`MemberName`, emails, etc.) through the join and hash-grouping operations.
  - Every non-aggregated column in `SELECT` must be dragged into the `GROUP BY` list (`GROUP BY m.MemberKey, m.MemberName, m.CreditScore, m.DebtToIncomeRatio`).
  - If business stakeholders request 5 additional member columns tomorrow (e.g., `Email`, `Address`, `City`), you would be forced to modify both the `SELECT` and `GROUP BY` clauses.
- **Senior Best Practice ("The Lean CTE"):**
  1. **Pre-aggregate the Fact table inside the CTE first using ONLY the join surrogate key (`MemberKey`).**
  2. Filter and summarize rows at the numeric/key level (`COUNT(*)`, `SUM(OriginalAmount)`).
  3. **Join to the Dimension table in the outer query.** Because the CTE has already squashed thousands of loans into a few dozen qualifying member IDs, the join to `dimmember` touches only the surviving records and allows cherry-picking any dimensional attribute (`m.CreditScore`, `m.MemberName`, `m.Email`) without touching `GROUP BY`.

---

### 💡 Credit Score & Dimensional Attributes
- `CreditScore` is an atomic, dimensional attribute originating from the credit bureau and stored directly on `dbo.dimmember`.
- It does not need any formula calculation or row-level math; once the lean summary is joined to `dimmember`, it is projected directly (`m.CreditScore`).

---

### 🛑 Precision & Aggregate Functions: `COUNT(*)` vs. `COUNT(col)`
- `COUNT(l.LoanType)` will silently skip records if `LoanType` is ever `NULL`.
- Using `COUNT(*)` explicitly counts the number of loan rows for that member, which is the exact business requirement.

---

## 3. Approved Production Solution (Lean CTE Architecture)

```sql
WITH loans_summary AS (
    SELECT 
        l.MemberKey,
        COUNT(*)                         AS active_loan_count,
        ROUND(SUM(l.OriginalAmount), 2)  AS total_exposure
    FROM dbo.dimloan l
    GROUP BY l.MemberKey
    HAVING COUNT(*) > 1 
       AND SUM(l.OriginalAmount) > 30000
)
SELECT 
    m.MemberName         AS member_name,
    m.CreditScore        AS credit_score,
    m.DebtToIncomeRatio  AS debt_to_income,
    ls.active_loan_count,
    ls.total_exposure
FROM loans_summary ls
INNER JOIN dbo.dimmember m 
    ON ls.MemberKey = m.MemberKey
ORDER BY ls.total_exposure DESC;
```
