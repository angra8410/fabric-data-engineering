# Code Review & Deep Dive Log: Lesson 1.8 (Database Internals, B-Trees & Performance Tuning)

- **Date:** 2026-09-19
- **Topic:** Storage Engines, 8KB Pages, Clustered vs. Non-Clustered Indexes, Index Seek vs. Scan, SARGability, and Multi-Engine Percentiles
- **Domain:** Banking Core Database (`BANKS`, `BankTransactions`, SSMS Execution Plans)
- **Module:** Módulo 1: SQL & Query Engineering (Fase 1.4 & 1.5)

---

## 1. Physical Storage Internals: How Databases Actually Store Data

### 📦 8 KB Pages and the Database File
In relational engines like SQL Server:
- All database data resides in `.mdf` (primary) and `.ndf` (secondary) disk files.
- Storage space inside these files is divided into contiguous **8 KB blocks called "Pages"**.
- A table can only exist on disk in **one of two physical states**:

```
                                 [ Table Storage States ]
                                      /           \
                                     /             \
                  [ State 1: A Heap ]               [ State 2: A Clustered Index ]
                  • Unsorted pile of rows.          • Data physically organized as a B-Tree.
                  • New rows land on any page.      • The Leaf Level IS the actual table.
                  • Every search = Table Scan.      • Fast searches = Index Seek (O(log N)).
```

---

## 2. The Clustered Index Reality: "There is No Separate Table"

A common misconception is that an index is always an "extra helper table".

- **The Clustered Index IS the Table:**
  When you create a Clustered Index on a table, SQL Server physically sorts the table's actual data pages on disk into a **B-Tree (Balanced Tree)** structure.

```
                      [ Root Page (8 KB) ]
                    /                      \
          [ Intermediate Page ]      [ Intermediate Page ]
                /          \               /          \
          [ Leaf Page 1 ] [ Leaf Page 2 ] [ Leaf Page 3 ] [ Leaf Page 4 ]
          ───────────────────────────────────────────────────────────────
          ▲
          └── THE LEAF PAGES ARE THE ACTUAL ROWS OF YOUR TABLE!
              (All columns: ID, Name, Country, Balance, etc. live here)
```

### 📚 The Definitive Analogy:
| Structure | Real-World Analogy | Does it duplicate data on disk? |
| :--- | :--- | :--- |
| **Clustered Index** | **The Phone Book itself.**<br>The phone book is printed in alphabetical order by last name. The phone book *is* the clustered index. | **NO.** It organizes the table's existing physical data pages. |
| **Non-Clustered Index** | **The Index at the back of a Textbook.**<br>A separate 10-page section at the end of the book pointing to specific page numbers in the main text. | **YES.** It creates an independent, smaller B-Tree holding only the indexed key + pointers back to the main table. |

---

## 3. Query Complexity: Index Seek vs. Clustered Index Scan

| Operation | Complexity | Physical Action | Scaling Behavior |
| :--- | :--- | :--- | :--- |
| **Clustered Index Seek** | **$O(\log N)$** (Logarithmic) | Hops down the B-Tree levels (Root $\rightarrow$ Intermediate $\rightarrow$ Leaf) to land directly on the row. | **Virtually Constant:**<br>10 rows = 1–2 page reads.<br>1,000,000 rows = ~3 page reads.<br>10,000,000 rows = ~4 page reads. |
| **Clustered Index Scan** | **$O(N)$** (Linear) | Reads every single leaf page of the table from start to finish. | **Directly Proportional:**<br>Double the rows $\rightarrow$ double the I/O disk reads. |

### Verification in SSMS Execution Plan (Ctrl + M):
- `SELECT * FROM BANKS WHERE BNK_ID = 1;` $\rightarrow$ **Clustered Index Seek**
- `SELECT * FROM BANKS WHERE BNK_COUNTRY = 'India';` (without index) $\rightarrow$ **Clustered Index Scan**

---

## 4. Architectural Decision: Primary Key as Clustered Index

By default, SQL Server assigns the Clustered Index to the `PRIMARY KEY`.

### When it is IDEAL:
1. **Sequential / Auto-Incrementing Integers (`IDENTITY`):**
   - New rows are appended to the end of the final page.
   - Prevents **Page Splits** (the expensive disk operation where SQL Server has to rip an 8KB page in half to insert a row in the middle).
2. **Narrow Keys (4-byte `INT`):**
   - Secondary (non-clustered) indexes use the clustered key as their pointer. A small clustered key keeps all secondary indexes fast and compact in RAM.

### When to OVERRIDE (Decouple PK from Clustered Index):
1. **Random GUIDs (`NEWID()`):** Inserting random strings causes constant page splits and fragmented disks. Make the GUID PK `NONCLUSTERED`.
2. **Time-Series / Transaction Tables:**
   - Queries almost never look for a single transaction ID; they query date ranges (`WHERE tx_date BETWEEN '2026-01-01' AND '2026-01-31'`).
   - **Architectural Solution:** Make the PK `NONCLUSTERED` on `TransactionID`, and make the `CLUSTERED INDEX` on `TransactionDate`. This forces all January transactions to sit physically side-by-side on disk for blazing fast range reads.

---

## 5. Multi-Engine Percentiles Comparison

Why do percentiles feel different across database engines?

```sql
-- 1. SQL Server / T-SQL (Window Analytic Function)
SELECT 
    BranchID,
    Amount,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY Amount) OVER (PARTITION BY BranchID) AS Median_Continuous,
    PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY Amount) OVER (PARTITION BY BranchID) AS Median_Discrete
FROM dbo.factloantransactions;

-- 2. Microsoft Fabric Lakehouse / PySpark (Distributed Approximation)
-- Avoids sorting billions of rows onto a single worker node
df_percentiles = df_tx.selectExpr(
    "percentile_approx(tx_amount, array(0.25, 0.50, 0.75), 10000) AS quartiles"
)

-- 3. SQLite
-- No native PERCENTILE_CONT/DISC. Must be calculated via NTILE(100) or window rank approximations.
```
