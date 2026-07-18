-- Fabric notebook source

-- METADATA ********************

-- META {
-- META   "kernel_info": {
-- META     "name": "synapse_pyspark"
-- META   },
-- META   "dependencies": {
-- META     "lakehouse": {
-- META       "default_lakehouse": "cd23cf30-fd21-42d0-822e-530bdc5993d8",
-- META       "default_lakehouse_name": "AdventureWorks_Dev_LH",
-- META       "default_lakehouse_workspace_id": "8dee4490-4f0e-468b-9a33-10b32f49df49",
-- META       "known_lakehouses": [
-- META         {
-- META           "id": "cd23cf30-fd21-42d0-822e-530bdc5993d8"
-- META         }
-- META       ]
-- META     },
-- META     "warehouse": {
-- META       "known_warehouses": []
-- META     }
-- META   }
-- META }

-- MARKDOWN ********************

-- # AdventureWorks SQL Practice Sandbox Notebook
-- 
-- Welcome to your private SQL testing playground! This notebook has been custom-tailored with 10 database engineering tasks mapped directly to your active **AdventureWorks_Dev_LH** schemas.
-- 
-- ### Instructions:
-- 1. Attach this notebook to your active Lakehouse in Microsoft Fabric.
-- 2. Review the constraints and hints inside each Markdown header.
-- 3. Write your query solutions inside the designated `%%sql` code cells.
-- 4. Press **Ctrl + Enter** to execute and validate your query against the active databases!

-- MARKDOWN ********************

-- ## 1. Simple Filtering & Sorting
-- 
-- * **Original Question:** Retrieve all records from `employees` where `age > 30` ordered by `age DESC`.
-- * **Your Adapted Task:** Write an SQL query to retrieve all records from `AdventureWorks_Dev_LH.Person.Person` where the `EmailPromotion` column is equal to `2`. Sort the final results by `BusinessEntityID` in descending order.
-- * **Key Columns:** `BusinessEntityID`, `EmailPromotion`
-- * **Hint:** Use standard `WHERE` filtering and `ORDER BY ... DESC` to sequence the data high-to-low.

-- CELL ********************

-- MAGIC %%sql
-- MAGIC -- Write your SQL query below:
-- MAGIC SELECT * FROM AdventureWorks_Dev_LH.Person.Person
-- MAGIC WHERE Person.EmailPromotion = 2


-- METADATA ********************

-- META {
-- META   "language": "sparksql",
-- META   "language_group": "synapse_pyspark"
-- META }

-- MARKDOWN ********************

-- ## 2. Relational Aggregations (`GROUP BY` & `JOIN`)
-- 
-- * **Original Question:** Find the total number of employees in each department.
-- * **Your Adapted Task:** Write an SQL query to find the total number of products in each `Color` bucket from `AdventureWorks_Dev_LH.Production.Product`. Your query should:
--   1. Display the color name.
--   2. Display the count of products.
--   3. Clean up any missing (`NULL`) colors to read `'Multi-Tone'` instead of a blank index slot.
-- * **Key Columns:** `ProductID`, `Color`
-- * **Hint:** Consider using standard database functions like `COALESCE` or conditional `CASE WHEN` logic to map `NULL` values before applying your `GROUP BY` collection rules.

-- CELL ********************

SELECT 
    CASE WHEN p.Color IS NULL THEN 'Multi-tone' ELSE p.Color END AS CleanedColor,
    COUNT(*) AS Count_Products
FROM AdventureWorks_Dev_LH.Production.Product AS p 
GROUP BY CleanedColor
ORDER BY Count_Products DESC

-- METADATA ********************

-- META {
-- META   "language": "sparksql",
-- META   "language_group": "synapse_pyspark"
-- META }

-- MARKDOWN ********************

-- ## 3. Date/Group Aggregations & Top-N Limiting
-- 
-- * **Original Question:** Find the date with the highest total sales amount.
-- * **Your Adapted Task:** Write an SQL query using `AdventureWorks_Dev_LH.Sales.SalesOrderDetail` to find the single `ProductID` that has the absolute highest total ordered quantity (`SUM(OrderQty)`).
-- * **Key Columns:** `ProductID`, `OrderQty`
-- * **Hint:** Group elements by product, calculate structural column totals using aggregate addition, order the metrics descending, and restrict the engine to outputting only the single highest row index using standard limiting limits.

-- CELL ********************

-- MAGIC %%sql
-- MAGIC -- Write your SQL query below:
-- MAGIC SELECT p.ProductID, SUM(p.OrderQty) AS OrderQuantity
-- MAGIC FROM AdventureWorks_Dev_LH.Sales.SalesOrderDetail p
-- MAGIC GROUP BY p.ProductID
-- MAGIC ORDER BY OrderQuantity DESC
-- MAGIC LIMIT 1

-- METADATA ********************

-- META {
-- META   "language": "sparksql",
-- META   "language_group": "synapse_pyspark"
-- META }

-- MARKDOWN ********************

-- ## 4. Finding Missing Relationships (The Anti-Join)
-- 
-- * **Original Question:** List the names of employees who have never completed a task.
-- * **Your Adapted Task:** Write an SQL query to list the names of products in `AdventureWorks_Dev_LH.Production.Product` that have **never** been ordered (meaning their `ProductID` does not exist anywhere in the transaction tables within `AdventureWorks_Dev_LH.Sales.SalesOrderDetail`).
-- * **Key Columns:**
--   * `AdventureWorks_Dev_LH.Production.Product` (`ProductID`, `Name`)
--   * `AdventureWorks_Dev_LH.Sales.SalesOrderDetail` (`ProductID`)
-- * **Hint:** Try connecting your product registry with the sales ledger using a `LEFT JOIN` on the matching key, then filter for rows where the matching sales transaction side registers `IS NULL`. Alternatively, prove your mastery by writing this using a nested `NOT EXISTS` subquery.

-- CELL ********************

-- MAGIC %%sql
-- MAGIC -- Write your SQL query below:
-- MAGIC SELECT p.Name
-- MAGIC FROM AdventureWorks_Dev_LH.Production.Product p
-- MAGIC WHERE NOT EXISTS (
-- MAGIC     SELECT 1
-- MAGIC FROM AdventureWorks_Dev_LH.Sales.SalesOrderDetail s 
-- MAGIC WHERE p.ProductID=s.ProductID
-- MAGIC )

-- METADATA ********************

-- META {
-- META   "language": "sparksql",
-- META   "language_group": "synapse_pyspark"
-- META }

-- MARKDOWN ********************

-- ## 5. Finding the N-th Highest Record
-- 
-- * **Original Question:** Find the third highest salary from the `salaries` table.
-- * **Your Adapted Task:** Write an SQL query to find the **third highest distinct** product `ListPrice` from the `AdventureWorks_Dev_LH.Production.Product` table.
-- * **Key Columns:** `ListPrice`
-- * **Hint:** You can resolve this simply using standard `OFFSET` structures, or display senior engineering style by building an analytical CTE with the `DENSE_RANK()` window operator partitioned across price boundaries.

-- CELL ********************

-- MAGIC %%sql
-- MAGIC -- Write your SQL query below:
-- MAGIC SELECT
-- MAGIC FROM AdventureWorks_Dev_LH.Production.Product p
-- MAGIC 


-- METADATA ********************

-- META {
-- META   "language": "sparksql",
-- META   "language_group": "synapse_pyspark"
-- META }

-- MARKDOWN ********************

-- ## 6. Multi-Table Aggregation Join
-- 
-- * **Original Question:** Find the name of the most ordered product.
-- * **Your Adapted Task:** Join `AdventureWorks_Dev_LH.Production.Product` and `AdventureWorks_Dev_LH.Sales.SalesOrderDetail` to find the descriptive product `Name` that has the highest cumulative sum of `OrderQty` across all transactions.
-- * **Key Columns:**
--   * `AdventureWorks_Dev_LH.Production.Product` (`ProductID`, `Name`)
--   * `AdventureWorks_Dev_LH.Sales.SalesOrderDetail` (`ProductID`, `OrderQty`)
-- * **Hint:** Declare brief table aliases to keep your join connections clean. Group on the descriptive string name and aggregate the metric before limiting your sorted data view.

-- CELL ********************

-- MAGIC %%sql
-- MAGIC -- Write your SQL query below:
-- MAGIC 


-- METADATA ********************

-- META {
-- META   "language": "sparksql",
-- META   "language_group": "synapse_pyspark"
-- META }

-- MARKDOWN ********************

-- ## 7. Filtering Aggregated Groups (`HAVING`)
-- 
-- * **Original Question:** Find average salary in each department, but only for departments with > 5 employees.
-- * **Your Adapted Task:** Write an SQL query that displays the average `ListPrice` of products grouped by `Color` from `AdventureWorks_Dev_LH.Production.Product`, but only for color groups that contain **more than 10** products. Completely exclude `NULL` colors from your output.
-- * **Key Columns:** `Color`, `ListPrice`
-- * **Hint:** Remember the fundamental logical flow of SQL: `WHERE` filters raw tables before the engine groups the rows. To filter summarize statistics after they are grouped, you must apply a `HAVING` statement instead.

-- CELL ********************

-- MAGIC %%sql
-- MAGIC -- Write your SQL query below:
-- MAGIC 


-- METADATA ********************

-- META {
-- META   "language": "sparksql",
-- META   "language_group": "synapse_pyspark"
-- META }

-- MARKDOWN ********************

-- ## 8. Self-Joins (Relationship Matches)
-- 
-- * **Original Question:** Find all employees who are also managers (self-referencing table).
-- * **Your Adapted Task:** Write an SQL query to perform a self-join on `AdventureWorks_Dev_LH.Production.Product` to find pairs of **different** products (`ProductID` is different) that share the **exact same** non-zero `ListPrice` value.
-- * **Key Columns:** `ProductID`, `Name`, `ListPrice`
-- * **Hint:** Declare your target table twice using unique aliases (like `Product p1 JOIN Product p2`). Ensure you prevent products from matching with themselves (`p1.ProductID <> p2.ProductID`), and filter out free catalog elements (`ListPrice > 0`).

-- CELL ********************

-- MAGIC %%sql
-- MAGIC -- Write your SQL query below:
-- MAGIC 


-- METADATA ********************

-- META {
-- META   "language": "sparksql",
-- META   "language_group": "synapse_pyspark"
-- META }

-- MARKDOWN ********************

-- ## 9. Data Modification (Conditional Update)
-- 
-- * **Original Question:** Update employee status to 'Inactive' for users who haven't logged in for a year.
-- * **Your Adapted Task:** Write an SQL query to update the `ListPrice` of all products in `AdventureWorks_Dev_LH.Production.Product` to be 10% higher, but **only** for products whose `Color` is currently registered as `'Red'`.
-- * **Key Columns:** `Color`, `ListPrice`
-- * **Hint:** Utilize the standard Data Modification Language `UPDATE` statement mapping calculations to the column setter, backed by red string checks.

-- CELL ********************

-- MAGIC %%sql
-- MAGIC -- Write your SQL query below:
-- MAGIC 


-- METADATA ********************

-- META {
-- META   "language": "sparksql",
-- META   "language_group": "synapse_pyspark"
-- META }

-- MARKDOWN ********************

-- ## 10. Data Modification (Purging Records)
-- 
-- * **Original Question:** Delete all records from `temporary_logs` older than one month.
-- * **Your Adapted Task:** Write an SQL query to delete all records from a hypothetical staging table `AdventureWorks_Dev_LH.Sales.TemporaryOrderLogs` where the `LogDate` timestamp is older than 6 months.
-- * **Key Columns:** `LogDate`
-- * **Hint:** Build a `DELETE FROM` query and compare the target date column against intervals relative to the current timestamp using date arithmetic (e.g., `CURRENT_DATE() - INTERVAL 6 MONTH`).

-- CELL ********************

-- MAGIC %%sql
-- MAGIC -- Write your SQL query below:
-- MAGIC 


-- METADATA ********************

-- META {
-- META   "language": "sparksql",
-- META   "language_group": "synapse_pyspark"
-- META }

-- CELL ********************

SELECT p.Name, p.ListPrice
FROM AdventureWorks_Dev_LH.Production.Product p 
WHERE p.ListPrice > (SELECT AVG(sp.ListPrice) FROM AdventureWorks_Dev_LH.Production.Product sp)


-- METADATA ********************

-- META {
-- META   "language": "sparksql",
-- META   "language_group": "synapse_pyspark"
-- META }

-- CELL ********************

SELECT p.Name, p.ListPrice
FROM AdventureWorks_Dev_LH.Production.Product p
WHERE p.ListPrice > (SELECT AVG(sp.ListPrice) FROM AdventureWorks_Dev_LH.Production.Product sp)

-- METADATA ********************

-- META {
-- META   "language": "sparksql",
-- META   "language_group": "synapse_pyspark"
-- META }

-- CELL ********************

SELECT p.Name, p.ListPrice - (SELECT AVG(sp.ListPrice) FROM AdventureWorks_Dev_LH.Production.Product sp ) AS PriceDifference
FROM AdventureWorks_Dev_LH.Production.Product p

-- METADATA ********************

-- META {
-- META   "language": "sparksql",
-- META   "language_group": "synapse_pyspark"
-- META }

-- MARKDOWN ********************

-- Challenge 1C: Scalar Subquery in the HAVING Clause (Group Filtering)
-- 
-- The Scenario
-- 
-- You are analyzing pricing trends across product colors. You want to identify which color categories are premium—meaning their specific group's average price is higher than the average price of all inventory items combined.
-- 
-- The Objective
-- 
-- Write an SQL query that groups products by Color and calculates their average price. Use a scalar subquery to filter the final grouped results, displaying only those color categories whose average list price is strictly greater than the overall average list price of all products in the database. Exclude NULL colors.
-- 
-- Key Table & Columns
-- 
-- AdventureWorks_Dev_LH.Production.Product (Color, ListPrice)
-- 
-- Conceptual Blueprint
-- 
-- Filter out NULL colors using WHERE Color IS NOT NULL.
-- 
-- Group by Color and select Color and AVG(ListPrice).
-- 
-- Filter the aggregated average in your HAVING clause against your scalar subquery:
-- HAVING AVG(ListPrice) > (SELECT AVG(ListPrice) FROM ...)

-- CELL ********************

SELECT 
p.Color, AVG(p.ListPrice) - (SELECT AVG(sp.ListPrice) FROM AdventureWorks_Dev_LH.Production.Product sp )
FROM AdventureWorks_Dev_LH.Production.Product p
WHERE p.Color IS NOT NULL
GROUP BY p.Color


-- METADATA ********************

-- META {
-- META   "language": "sparksql",
-- META   "language_group": "synapse_pyspark"
-- META }

-- MARKDOWN ********************

-- The Scenario
-- 
-- The product management team wants to evaluate our high-end inventory. They want you to compare all products against a specific benchmark: the average cost of our Yellow products. They want to see both the product's name and how much more expensive it is compared to the Yellow baseline.
-- 
-- The Objective
-- 
-- Write an SQL query to retrieve the Name, ListPrice, and a calculated column called PriceDifferenceYellow of all products in AdventureWorks_Dev_LH.Production.Product whose ListPrice is strictly greater than the average ListPrice of products whose Color is 'Yellow'.
-- 
-- Key Columns
-- 
-- AdventureWorks_Dev_LH.Production.Product (Name, ListPrice, Color)
-- 
-- The Conveyor Belt Roadmap
-- 
-- FROM: Load Production.Product.
-- 
-- WHERE: Run the subquery to find the average price of only Yellow products (e.g., $520.42$). Filter out any raw product from the main conveyor belt whose price is lower than or equal to that number.
-- 
-- SELECT: Take the surviving products, subtract the Yellow average subquery from their individual ListPrice, and output the result as PriceDifferenceYellow.


-- CELL ********************

SELECT p.Name, p.ListPrice,
p.ListPrice - (SELECT AVG(sp.ListPrice) FROM AdventureWorks_Dev_LH.Production.Product sp WHERE sp.Color = 'Yellow' ) AS PriceDifferenceYellow
FROM AdventureWorks_Dev_LH.Production.Product p
WHERE p.ListPrice > (SELECT AVG(sp.ListPrice) FROM AdventureWorks_Dev_LH.Production.Product sp WHERE sp.Color = 'Yellow')
ORDER BY p.Color


-- METADATA ********************

-- META {
-- META   "language": "sparksql",
-- META   "language_group": "synapse_pyspark"
-- META }

-- MARKDOWN ********************

-- ## Excercise 1E

-- CELL ********************

SELECT 
p.Name, 
p.ListPrice
FROM AdventureWorks_Dev_LH.Production.Product p  
WHERE p.ListPrice > (SELECT AVG(sp.ListPrice) FROM AdventureWorks_Dev_LH.Production.Product AS sp WHERE sp.Color = 'Black')
AND p.ListPrice < (SELECT AVG(sp.ListPrice) FROM AdventureWorks_Dev_LH.Production.Product AS sp WHERE sp.Color = 'Red')
                                                                           


-- METADATA ********************

-- META {
-- META   "language": "sparksql",
-- META   "language_group": "synapse_pyspark"
-- META }

-- MARKDOWN ********************

-- ## Challenge 1F: Subcategory Group Averages vs. Global Baseline (HAVING + Filtered Outer)

-- MARKDOWN ********************

-- ## The Scenario
-- 
-- You are analyzing performance across different product subcategories. You want to identify "high-value subcategories"—meaning the subcategory's collective average price is higher than the company-wide average price.
-- 
-- ## The Objective
-- 
-- Write an SQL query that groups products by their ProductSubcategoryID and calculates their average price. Use a scalar subquery to display only those subcategories whose average list price is strictly greater than the overall average list price of all products combined. Exclude NULL subcategories.
-- 
-- ## Key Columns
-- 
-- AdventureWorks_Dev_LH.Production.Product (ProductSubcategoryID, ListPrice)
-- 
-- The Conveyor Belt Roadmap
-- 
-- FROM: Load the table.
-- 
-- WHERE: Filter out raw rows where ProductSubcategoryID IS NOT NULL.
-- 
-- GROUP BY: Collapse remaining rows into ProductSubcategoryID buckets.
-- 
-- HAVING: Compare the collective average price of each bucket (AVG(p.ListPrice)) against a scalar subquery that calculates the overall global average of all products.
-- 
-- SELECT: Display the subcategory ID and its calculated group average.


-- CELL ********************

SELECT 
p.ProductSubcategoryID, 
AVG(p.ListPrice) AS SubcategoryPrice
FROM AdventureWorks_Dev_LH.Production.Product p
WHERE p.ProductSubcategoryID IS NOT NULL
GROUP BY p.ProductSubcategoryID
HAVING AVG(p.ListPrice) > (SELECT AVG(sp.ListPrice) FROM AdventureWorks_Dev_LH.Production.Product sp)

-- METADATA ********************

-- META {
-- META   "language": "sparksql",
-- META   "language_group": "synapse_pyspark"
-- META }

-- MARKDOWN ********************

-- ## Challenge 1G: The Correlated Row-by-Row Exporter (EXISTS Safety)

-- MARKDOWN ********************

-- ## The Scenario: 

-- MARKDOWN ********************

-- ##### The logistics team wants a fast, optimized list of products that have recorded order quantities of exactly 1 unit at any point in history.

-- MARKDOWN ********************

-- ## The Objective:

-- MARKDOWN ********************

-- ##### Write an SQL query to select the Name and ProductNumber of products in AdventureWorks_Dev_LH.Production.Product where at least one transaction record exists in AdventureWorks_Dev_LH.Sales.SalesOrderDetail with an OrderQty equal to 1. Warning: Do not use JOIN or IN here. Use EXISTS!

-- CELL ********************

SELECT p.Name, p.ProductNumber
FROM AdventureWorks_Dev_LH.Production.Product p
WHERE EXISTS (SELECT 1
FROM AdventureWorks_Dev_LH.Sales.SalesOrderDetail s
WHERE s.OrderQty = 1 AND p.ProductID=s.ProductID )

-- METADATA ********************

-- META {
-- META   "language": "sparksql",
-- META   "language_group": "synapse_pyspark"
-- META }

-- MARKDOWN ********************

-- ## Challenge 1H: Target Deviations with In-Query Math (SELECT vs. WHERE Syncing)

-- MARKDOWN ********************

-- ### The Scenario
-- 
-- You are assisting the retail team in designing an aggressive promotion. They want to compare all products against our Low-Class (Class = 'L') products. They want to see each product's price alongside a column showing how many dollars cheaper or more expensive it is compared to that low-class baseline.

-- MARKDOWN ********************

-- ### The Objective
-- 
-- Write an SQL query to retrieve the Name, ListPrice, and a calculated column called DeviationFromLowClass of all products. Do not filter out any rows—the retail team wants to see every single product, even if its deviation is negative or zero.

-- MARKDOWN ********************

-- ### Key Columns
-- 
-- AdventureWorks_Dev_LH.Production.Product (Name, ListPrice, Class)
-- 
-- The Conveyor Belt Roadmap
-- 
-- FROM: Load Production.Product.
-- 
-- WHERE: Trick question! Do not write a WHERE filter because we want to see the entire inventory catalog.
-- 
-- SELECT: For every row, subtract the average price of Low-Class products from the individual product price:
-- p.ListPrice - (SELECT AVG(sp.ListPrice) FROM AdventureWorks_Dev_LH.Production.Product sp WHERE sp.Class = 'L')
-- 
-- ORDER BY: Sort the final results with the most expensive deviations at the top.

-- CELL ********************

SELECT 
p.Name, 
p.ListPrice,
p.ListPrice - (SELECT AVG(sp.ListPrice) FROM AdventureWorks_Dev_LH.Production.Product sp WHERE TRIM(sp.Class) = 'L' ) AS DeviationFromLowClass
FROM AdventureWorks_Dev_LH.Production.Product p

-- METADATA ********************

-- META {
-- META   "language": "sparksql",
-- META   "language_group": "synapse_pyspark"
-- META }

-- MARKDOWN ********************

-- ## Challenge 1I: The Senior-Level Trap (Anti-Join NULL Safety)

-- MARKDOWN ********************

-- ### The Scenario
-- 
-- This is the ultimate test of SQL logical safety. The shipping department wants a list of product subcategories that have never had a product assigned to them.
-- 
-- Crucial Warning: If you use NOT IN, and there is even a single NULL subcategory in the product table, the query will return 0 rows incorrectly due to three-valued logic. You must write this using the bulletproof NOT EXISTS correlation pattern.

-- MARKDOWN ********************

-- ### The Objective
-- 
-- Write an SQL query to select the Name of all subcategories in AdventureWorks_Dev_LH.Production.ProductSubcategory that do not have any products pointing to them in the AdventureWorks_Dev_LH.Production.Product table.

-- MARKDOWN ********************

-- ### Key Tables & Columns
-- 
-- AdventureWorks_Dev_LH.Production.ProductSubcategory as ps (ProductSubcategoryID, Name)
-- 
-- AdventureWorks_Dev_LH.Production.Product as p (ProductSubcategoryID)
-- 
-- The Conveyor Belt Roadmap
-- 
-- FROM: Load the subcategory directory table ps.
-- 
-- WHERE NOT EXISTS: Run a row-by-row check against the product table p.
-- 
-- Correlation link: Match p.ProductSubcategoryID = ps.ProductSubcategoryID.
-- 
-- SELECT: Print the names of the abandoned subcategories.

-- CELL ********************

SELECT ps.Name AS UnusedSubcategoryName
FROM AdventureWorks_Dev_LH.Production.ProductSubcategory ps
WHERE NOT EXISTS (
    SELECT 1 
    FROM AdventureWorks_Dev_LH.Production.Product p
    WHERE p.ProductSubcategoryID = ps.ProductSubcategoryID
)

-- METADATA ********************

-- META {
-- META   "language": "sparksql",
-- META   "language_group": "synapse_pyspark"
-- META }

-- MARKDOWN ********************

-- # The Objective
-- Write an SQL query to retrieve all records from AdventureWorks_Dev_LH.Person.Person where the EmailPromotion column is equal to 2. Sort the final results by BusinessEntityID in descending order.

-- CELL ********************

SELECT *
FROM AdventureWorks_Dev_LH.Person.Person p
WHERE p.EmailPromotion = 2
ORDER BY BusinessEntityID DESC

-- METADATA ********************

-- META {
-- META   "language": "sparksql",
-- META   "language_group": "synapse_pyspark"
-- META }

-- MARKDOWN ********************

-- # 2. Relational Aggregations (GROUP BY & JOIN)

-- MARKDOWN ********************

-- ### Original Question: Find the total number of employees in each department.
-- 
-- Your Adapted Task: Write an SQL query to find the total number of products in each Color bucket from AdventureWorks_Dev_LH.Production.Product. Your query should:
-- 
-- Display the color name.
-- 
-- Display the count of products.
-- 
-- Clean up any missing (NULL) colors to read 'Multi-Tone'.
-- 
-- Key Schemas: AdventureWorks_Dev_LH.Production.Product (ProductID, Color)

-- CELL ********************

SELECT 
    COALESCE(p.Color, 'Multi-Tone') AS Color,
    COUNT(*) AS CountOfProducts
FROM AdventureWorks_Dev_LH.Production.Product p
GROUP BY COALESCE(p.Color, 'Multi-Tone')
ORDER BY CountofProducts DESC;

-- METADATA ********************

-- META {
-- META   "language": "sparksql",
-- META   "language_group": "synapse_pyspark"
-- META }

-- MARKDOWN ********************

-- # 3. Date/Group Aggregations & Top-N Limiting

-- MARKDOWN ********************

-- ### Original Question: Find the date with the highest total sales amount.
-- 
-- Your Adapted Task: Write an SQL query using AdventureWorks_Dev_LH.Sales.SalesOrderDetail to find the single ProductID that has the absolute highest total ordered quantity (SUM(OrderQty)).
-- 
-- Key Schemas: AdventureWorks_Dev_LH.Sales.SalesOrderDetail (ProductID, OrderQty)
-- 
-- Hint: Group by the product, sum up the quantities, sort them in descending order, and limit the final results to just the top 1 row.

-- CELL ********************

SELECT s.ProductID, SUM(s.OrderQty) AS TotalQtyOrdered
FROM AdventureWorks_Dev_LH.Sales.SalesOrderDetail s
GROUP BY s.ProductID
ORDER BY TotalQtyOrdered DESC
LIMIT 1

-- METADATA ********************

-- META {
-- META   "language": "sparksql",
-- META   "language_group": "synapse_pyspark"
-- META }

-- MARKDOWN ********************

-- #

-- MARKDOWN ********************

-- # 4. Finding Missing Relationships (The Anti-Join)

-- MARKDOWN ********************

-- ## Original Question: List the names of employees who have never completed a task.
-- 
-- Your Adapted Task: Write an SQL query to list the names of products in AdventureWorks_Dev_LH.Production.Product that have never been ordered (meaning their ProductID does not exist anywhere in the AdventureWorks_Dev_LH.Sales.SalesOrderDetail table).
-- 
-- Key Schemas:
-- 
-- AdventureWorks_Dev_LH.Production.Product (ProductID, Name)
-- 
-- AdventureWorks_Dev_LH.Sales.SalesOrderDetail (ProductID)
