# Code Review & Learning Log: Exercise 1.7 (Cumulative Running Totals & Window Framing)

- **Date:** 2026-09-15
- **Topic:** Cumulative Running Totals (`SUM() OVER (PARTITION BY ... ORDER BY ...)`), Window Frame Specifications (`ROWS` vs. `RANGE`), Precision Control
- **Domain:** Credit Union / Loan Portfolio Analytics (`dbo.dimloan` & `dbo.dimmember`)

---

## 1. Business Requirement & Challenge Prompt

### 📋 Challenge 1.7 Prompt & Requirements
The Treasury & Portfolio Risk team wants to monitor borrower credit accumulation over time. They want to see each member's loans chronologically and observe their **cumulative loan exposure** (running total of loan amounts) growing with each new loan.

**Specific Output Requirements:**
- **Source Tables:** `dbo.dimloan` (`dl`) and `dbo.dimmember` (`dm`).
- **Business Metrics:**
  - For each member, calculate the chronological running total of `OriginalAmount` up to and including the current loan.
  - Name this calculated column `cumulative_loan_amount` (rounded to 2 decimal places).
- **Required Output Columns:**
  - `MemberName`
  - `MemberKey`
  - `LoanKey`
  - `LoanType`
  - `StartDate`
  - `OriginalAmount`
  - `cumulative_loan_amount`
- **Deterministic Sorting:**
  - Order the final report by `MemberName ASC`, `MemberKey ASC`, `StartDate ASC`, `LoanKey ASC`.

---

### 💡 Architectural Deep-Dive & Key Concepts

#### 1. Default Window Frame Trap: `RANGE` vs. `ROWS`
When you include an `ORDER BY` clause inside an `OVER(...)` specification without explicitly declaring a frame, the SQL standard defaults to:
```sql
RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
```
- **The Performance Trap:** In many SQL engines (including SQL Server / Microsoft Fabric T-SQL), `RANGE` requires spooling temporary tables to tempdb/storage to resolve duplicates across ties in the sort key.
- **The Analytical Duplicates Trap:** If two loans share the exact same `StartDate`, `RANGE` treats them as ties and aggregates both rows simultaneously, giving both identical running totals!
- **The Production Fix:** Explicitly declare the physical row frame:
  ```sql
  ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
  ```
  This is processed in-memory (far more performant) and computes a true, row-by-row cumulative progression.

---

## 2. Candidate Submission

*(Pending candidate query submission)*

```sql
-- Paste your candidate submission here when ready
```

---

## 3. Senior PR Review Analysis

*(To be completed upon submission)*

---

## 4. Approved Production Solution Reference

*(To be reviewed and finalized after candidate execution)*
