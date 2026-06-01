# Velykapet — Data Engineering Project

## Architecture
Bronze → Silver → Gold medallion on Microsoft Fabric (OneLake)

## Pipeline
`pl_labor_full_refresh` runs daily at 05:00 AM (Bogotá time)
Ingests `Data_Cliente_Multidominio.xlsx` → transforms → 
builds star schema → refreshes `test-velykapet` semantic model

## Layers
- **Bronze** (`lh_bronze_velykapet`): raw Excel ingestion
- **Silver** (`lh_silver_velykapet`): cleaned, typed, validated
- **Gold** (`lh_gold_velykapet`): star schema (dim_calendario, 
  dim_metodo_pago, gold_fct_ventas, gold_fct_gastos)

## Semantic Model
`test-velykapet` — DirectLake, 18 measures across 4 folders

## Owner
Antonio Gutierrez — contacto@velykapet.com