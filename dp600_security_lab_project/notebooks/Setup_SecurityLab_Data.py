# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse_name": "SecurityLab_Lakehouse"
# META     }
# META   }
# META }

# MARKDOWN ********************
# # DP-600 Study Environment: Security & Governance Lab
# ## Step 3 — Load Messy Synthetic Sales Data
# This notebook generates the synthetic `Sales` table with deliberate nulls, inconsistent casing, blank strings, and duplicate records for practicing Row-Level Security (RLS) and Object-Level Security (OLS).

# CELL ********************

from pyspark.sql import Row

data = [
    Row(SalesID=1, Region="East",  SalesRep="Alice", Email="alice@contoso.com", Amount=1200.00, CommissionPct=0.05),
    Row(SalesID=2, Region="east",  SalesRep="alice", Email="alice@contoso.com", Amount=950.0,   CommissionPct=0.05),
    Row(SalesID=3, Region="West",  SalesRep="Bob",   Email="bob@contoso.com",   Amount=None,    CommissionPct=0.04),
    Row(SalesID=4, Region="WEST",  SalesRep="Bob",   Email=None,                Amount=700.0,   CommissionPct=0.04),
    Row(SalesID=5, Region=None,    SalesRep="Carol", Email="carol@contoso.com", Amount=1100.0,  CommissionPct=None),
    Row(SalesID=6, Region="North", SalesRep="Carol", Email="carol@contoso.com", Amount=640.0,   CommissionPct=0.03),
    Row(SalesID=7, Region="",      SalesRep="Dave",  Email="dave@contoso.com",  Amount=2200.0,  CommissionPct=0.06),
    Row(SalesID=8, Region="West",  SalesRep="Dave",  Email="DAVE@CONTOSO.COM",  Amount=300.0,   CommissionPct=0.06),
    Row(SalesID=7, Region="East",  SalesRep="Dave",  Email="dave@contoso.com",  Amount=2200.0,  CommissionPct=0.06),
]

df = spark.createDataFrame(data)
df.write.mode("overwrite").format("delta").saveAsTable("Sales")

# METADATA ********************

# CELL ********************

# Verification query
display(spark.sql("SELECT * FROM Sales"))
print(f"Total Rows: {spark.sql('SELECT COUNT(*) FROM Sales').collect()[0][0]}")

# METADATA ********************
