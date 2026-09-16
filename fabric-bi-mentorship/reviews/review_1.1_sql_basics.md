# Code Review & Learning Log: Exercise 1.1 (SQL Fundamentals)

- **Date:** 2026-09-12
- **Topic:** Projections, Relational Joins, and SARGable Filtering
- **Domain:** Workforce / HR Analytics (Foundation)

---

## 1. Candidate Submission
```sql
SELECT 
    CONCAT(e.FirstName, ' ', e.LastName) AS FullName, 
    d.DepartmentName, 
    e.Salary
FROM Employees e
INNER JOIN Departments d ON e.DepartmentID=d.DeparmentID
WHERE e.HireDate > '2020-01-01'
GROUP BY d.DepartmentName, e.Salary
ORDER BY e.Salary DESC;
```

---

## 2. Senior PR Review Analysis

### 🛑 Issues Identified
1. **Unnecessary `GROUP BY` & Aggregate Syntax Error:**
   - Detailed queries (entity-level rows) should not use `GROUP BY` unless aggregating measures (`SUM`, `AVG`, `COUNT`).
   - Standard SQL engines reject unaggregated columns in the `SELECT` list (`e.FirstName`, `e.LastName`) that are missing from `GROUP BY`.
2. **Column Typo:**
   - `d.DeparmentID` missing `'t'` $\rightarrow$ `d.DepartmentID`.
3. **Join Decision Trap (`INNER` vs. `LEFT`):**
   - An `INNER JOIN` drops employees with unassigned departments (`DepartmentID IS NULL`), creating headcount reconciliation discrepancies with Payroll/Finance.
   - Senior standard: Use `LEFT JOIN` combined with `COALESCE(d.DepartmentName, 'Unassigned')`.

### ✅ Positive Takeaways
- **SARGable Date Filter:** `WHERE e.HireDate > '2020-01-01'` correctly avoids wrapping functions around indexed date columns, enabling engine partition/index pruning.
- Correct use of `CONCAT` over `+` operator to avoid unexpected `NULL` poisoning.

---

## 3. Approved Production Solution
```sql
SELECT 
    CONCAT_WS(' ', e.FirstName, e.LastName) AS employee_full_name, 
    COALESCE(d.DepartmentName, 'Unassigned') AS department_name, 
    e.Salary AS salary
FROM Employees e
LEFT JOIN Departments d 
    ON e.DepartmentID = d.DepartmentID
WHERE e.HireDate > '2020-01-01'
ORDER BY e.Salary DESC;
```
