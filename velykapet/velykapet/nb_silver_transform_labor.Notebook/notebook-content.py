# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "abe92425-50d3-48f4-baa0-ebbfadd93f25",
# META       "default_lakehouse_name": "lh_bronze_velykapet",
# META       "default_lakehouse_workspace_id": "b14581ac-9906-43e2-809c-c2fd4315ad5b",
# META       "known_lakehouses": [
# META         {
# META           "id": "abe92425-50d3-48f4-baa0-ebbfadd93f25"
# META         },
# META         {
# META           "id": "787ca3da-cb1e-4bc7-bcec-04cb2415e5d4"
# META         }
# META       ]
# META     }
# META   }
# META }

# CELL ********************

from pyspark.sql import functions as F
from pyspark.sql.types import DateType, DoubleType, StringType

# 1. Definición de Rutas ABFSS Base (Origen Bronze y Destino Silver)
base_abfss_path = "abfss://b14581ac-9906-43e2-809c-c2fd4315ad5b@onelake.dfs.fabric.microsoft.com/abe92425-50d3-48f4-baa0-ebbfadd93f25"

# Orígenes en Bronze
bronze_gastos_path = f"{base_abfss_path}/Tables/stg_gastos_raw"
bronze_ventas_path = f"{base_abfss_path}/Tables/stg_ventas_raw"

# Destinos en Silver (Escribimos directo a la sección Tables del OneLake)
silver_gastos_path = f"{base_abfss_path}/Tables/fct_gastos"
silver_ventas_path = f"{base_abfss_path}/Tables/fct_ventas"

print("Iniciando Transformación de Capa Silver Controlada mediante Rutas ABFSS...")

# ==========================================
# DOMINIO 1: TRANSFORMACIÓN DE GASTOS
# ==========================================
try:
    print("-> Procesando Hechos de GASTOS...")
    df_bronze_gastos = spark.read.format("delta").load(bronze_gastos_path)
    
    # Contrato de datos estricto y eliminación de columnas fantasmas (Unnamed)
    df_silver_gastos = df_bronze_gastos.select(
        F.col("Fecha").cast(DateType()).alias("fecha"),
        F.col("Descripción").cast(StringType()).alias("descripcion"),
        F.col("Categoría_gasto").cast(StringType()).alias("categoria_gasto"),
        F.col("Método_pago").cast(StringType()).alias("metodo_pago"),
        F.col("Monto_COP").cast(DoubleType()).alias("monto_cop"),
        F.col("Notas").cast(StringType()).alias("notas"),
        F.col("_nombre_pestaña").alias("origen_pestaña"),
        F.col("_fecha_ingestion").alias("fecha_ingestion_bronze"),
        F.current_timestamp().alias("fecha_procesado_silver")
    ).filter(F.col("fecha").isNotNull() | F.col("monto_cop").isNotNull())

    # ESCRITURA DIRECTA A ONELAKE (Inmune a SCHEMA_NOT_FOUND)
    df_silver_gastos.write \
        .format("delta") \
        .mode("overwrite") \
        .option("overwriteSchema", "true") \
        .save(silver_gastos_path)
        
    print(f"   [Éxito] Datos guardados físicamente en OneLake Silver: {silver_gastos_path}")

except Exception as e:
    print(f"   [Error] Fallo al transformar GASTOS en Silver: {str(e)}")
    raise e

# ==========================================
# DOMINIO 2: TRANSFORMACIÓN DE VENTAS (CALIBRADO)
# ==========================================
try:
    print("\n-> Procesando Hechos de VENTAS con esquema real...")
    df_bronze_ventas = spark.read.format("delta").load(bronze_ventas_path)
    
    # CONTRATO DE DATOS EXACTO PARA EL MODELO DE VENTAS DEL CLIENTE
    # Pasamos los strings de Bronze a tipos de datos analíticos reales
    df_silver_ventas = df_bronze_ventas.select(
        F.col("Año").cast(StringType()).alias("anio"),
        F.col("Fecha").cast(DateType()).alias("fecha"),
        F.col("Código_producto").cast(StringType()).alias("codigo_producto"),
        F.col("Producto").cast(StringType()).alias("producto"),
        F.col("Categoría").cast(StringType()).alias("categoria_producto"),
        F.col("Cantidad").cast(DoubleType()).alias("cantidad"),
        F.col("Precio_unitario_COP").cast(DoubleType()).alias("precio_unitario_cop"),
        F.col("Total_venta_COP").cast(DoubleType()).alias("total_venta_cop"),
        F.col("Costo_unitario_COP").cast(DoubleType()).alias("costo_unitario_cop"),
        F.col("Costo_total_COP").cast(DoubleType()).alias("costo_total_cop"),
        F.col("Utilidad_COP").cast(DoubleType()).alias("utilidad_cop"),
        F.col("Origen_ej_tienda_online").cast(StringType()).alias("canal_venta"),
        F.col("Método_de_pago").cast(StringType()).alias("metodo_pago"),
        F.col("Código_Transacción").cast(StringType()).alias("codigo_transaccion"),
        # Datos de entrega/logística (¡Muy valiosos para analítica de zonas!)
        F.col("Torre").cast(StringType()).alias("logistica_torre"),
        F.col("Apto").cast(StringType()).alias("logistica_apto"),
        F.col("Unidad").cast(StringType()).alias("logistica_unidad"),
        F.col("Notas").cast(StringType()).alias("notas"),
        # Trazabilidad
        F.col("_nombre_pestaña").alias("origen_pestaña"),
        F.col("_fecha_ingestion").alias("fecha_ingestion_bronze"),
        F.current_timestamp().alias("fecha_procesado_silver")
    ).filter(F.col("fecha").isNotNull() | F.col("total_venta_cop").isNotNull())

    # ESCRITURA DIRECTA A ONELAKE (Inmune a SCHEMA_NOT_FOUND)
    df_silver_ventas.write \
        .format("delta") \
        .mode("overwrite") \
        .option("overwriteSchema", "true") \
        .save(silver_ventas_path)
        
    print(f"   [Éxito] Datos de VENTAS guardados físicamente en OneLake Silver: {silver_ventas_path}")

except Exception as e:
    print(f"   [Error] Fallo al transformar VENTAS en Silver: {str(e)}")
    raise e

print("\n¡Capa Silver finalizada con éxito para GASTOS y VENTAS!")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
