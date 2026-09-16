# Code Review & Learning Log: Exercise 1.6 (Ranking Functions & Top-N Filtering)

- **Date:** 2026-09-15
- **Topic:** Ranking Functions (`DENSE_RANK()` vs. `ROW_NUMBER()`), Top-N Outer Filtering, Cardinality Guarantees
- **Domain:** Credit Union / Loan Portfolio Analytics (`dbo.dimloan` & `dbo.dimmember`)

---

## 1. Business Requirement & Candidate Submission

### 📋 Challenge 1.6 Prompt & Requirements
The Credit Risk committee wants to inspect exposure concentration at the individual borrower level:
> *"Retrieve the top 2 largest loans originated by each member."*

**Specific Output Requirements:**
- Source tables: `dbo.dimloan` and `dbo.dimmember`.
- Columns: `MemberName`, `LoanKey`, `LoanType`, `OriginalAmount`, `loan_rank`.
- Filter: Top 2 loans per member (`loan_rank <= 2`).
- Deterministic Ordering: `MemberName ASC`, then `loan_rank ASC`.

### Candidate Query
```sql
WITH rank_loans AS (
    SELECT
        l.MemberKey,
        l.LoanType,
        l.OriginalAmount,
        dense_rank() OVER (PARTITION BY l.MemberKey ORDER BY l.OriginalAmount DESC) AS loan_rank
        --(sum(l.OriginalAmount) OVER (PARTITION BY l.MemberKey )) AS loan_rank
    FROM 
        dimloan l 
)
SELECT 
    m.MemberName,
    m.MemberKey,
    rl.LoanType,
    rl.OriginalAmount,
    rl.loan_rank
FROM 
    rank_loans rl 
INNER JOIN dimmember m ON 
    rl.MemberKey = m.MemberKey;
```

---

## 2. Senior PR Review Analysis

### ✅ Positive Takeaways
1. **Accurate Window Partitioning & Inner Sort:**
   - Correctly partitioned by `l.MemberKey` and sorted by `l.OriginalAmount DESC` inside the window function:
     ```sql
     DENSE_RANK() OVER (PARTITION BY l.MemberKey ORDER BY l.OriginalAmount DESC)
     ```
2. **Proper CTE Staging for Window Filtering:**
   - Recognized that SQL engines evaluate `WHERE` before `SELECT` (window functions cannot be evaluated directly in the `WHERE` clause of the same query block). Wrapping the ranking calculation inside a CTE (`rank_loans`) was the correct design decision.

---

### 🛑 Issues Identified & Production Fixes

#### 1. Missing Top-N Outer Filter (`WHERE loan_rank <= 2`)
- **Observed Behavior:** In the execution output, records with `loan_rank = 3` are still returned (e.g., William Davis, Linda Jones, Lisa Brown all have their 3rd loan present).
- **The Cause:** The CTE calculated the rank, but the outer query did not filter on it.
- **Fix:** Add `WHERE rl.loan_rank <= 2` in the outer query block.

#### 2. `DENSE_RANK()` vs. `ROW_NUMBER()` (The Tie-Breaking / Cardinality Trap)
- **The Difference:**
  - `ROW_NUMBER()` assigns a unique, sequential integer ($1, 2, 3, \dots$) regardless of identical values.
  - `RANK()` leaves gaps on ties ($1, 2, 2, 4, \dots$).
  - `DENSE_RANK()` does not leave gaps on ties ($1, 2, 2, 3, \dots$).
- **The Risk:** If a member has multiple loans with the exact same `OriginalAmount` (e.g., two Auto loans of $25,000 tied for 2nd place), `DENSE_RANK() <= 2` will return **3 or more rows** for that borrower.
- **Production Standard:** If the business requirement strictly specifies *"at most 2 loans per borrower"* (strict cardinality), use `ROW_NUMBER()` with a deterministic secondary sort key (such as `LoanKey DESC`):
  ```sql
  ROW_NUMBER() OVER (
      PARTITION BY l.MemberKey 
      ORDER BY l.OriginalAmount DESC, l.LoanKey DESC
  ) AS loan_rank
  ```
  *(If business risk explicitly wants to see all ties, document `DENSE_RANK()` as a deliberate policy decision).*

#### 3. Column List Alignment (`LoanKey` vs. `MemberKey`)
- The requirements requested `LoanKey` to identify the loan entity. `LoanKey` was omitted from the CTE projection, and `MemberKey` was included in the final output instead.
- Include `l.LoanKey` in the CTE projection.

#### 4. The "Same-Name" Entity Resolution Trap (`MemberName` vs. `MemberKey`)
- **Observed Behavior on Execution:** In the candidate test run, two different members named `Anthony Johnson` (one with `MemberKey = 64` and the other with `MemberKey = 86`) had their loans interleaved in the results:
  - Row 3: Anthony Johnson (`64`), rank 1
  - Row 4: Anthony Johnson (`86`), rank 1
  - Row 5: Anthony Johnson (`64`), rank 2
- **The Cause:** Ordering only by `MemberName ASC, rl.loan_rank ASC` does not separate distinct people who share the same display name.
- **Production Best Practice:** Always include the primary/surrogate entity key in the `ORDER BY` (`ORDER BY m.MemberName ASC, m.MemberKey ASC, rl.loan_rank ASC`) to ensure individual customer portfolios remain grouped together deterministically.

---

## 3. Approved Production Solution
```sql
WITH ranked_member_loans AS (
    SELECT
        l.MemberKey,
        l.LoanKey,
        l.LoanType,
        l.OriginalAmount,
        ROW_NUMBER() OVER (
            PARTITION BY l.MemberKey 
            ORDER BY l.OriginalAmount DESC, l.LoanKey DESC
        ) AS loan_rank
    FROM dbo.dimloan l
)
SELECT 
    m.MemberName,
    m.MemberKey,
    rl.LoanKey,
    rl.LoanType,
    rl.OriginalAmount,
    rl.loan_rank
FROM ranked_member_loans rl
INNER JOIN dbo.dimmember m 
    ON rl.MemberKey = m.MemberKey
WHERE rl.loan_rank <= 2
ORDER BY 
    m.MemberName ASC, 
    m.MemberKey ASC, 
    rl.loan_rank ASC;
```
