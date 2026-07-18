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
# META   "language_group": "synapse_pyspark",
# META   "frozen": true,
# META   "editable": false
# META }

# CELL ********************

from pyspark.sql import functions as F
from pyspark.sql.types import DateType, DoubleType, StringType

# Definición de Rutas ABFSS Base (Origen Bronze y Destino Silver)
base_abfss_path = "abfss://b14581ac-9906-43e2-809c-c2fd4315ad5b@onelake.dfs.fabric.microsoft.com/abe92425-50d3-48f4-baa0-ebbfadd93f25"

# Orígenes en Bronze
bronze_gastos_path = f"{base_abfss_path}/Tables/stg_gastos_raw"
bronze_ventas_path = f"{base_abfss_path}/Tables/stg_ventas_raw"
bronze_compras_path = f"{base_abfss_path}/Tables/stg_compras_inventario_raw"
bronze_inventario_definitivo_path = f"{base_abfss_path}/Tables/stg_inventario_definitivo_raw"

# Destinos en Silver (Escribimos directo a la sección Tables del OneLake)
silver_gastos_path = f"{base_abfss_path}/Tables/fct_gastos"
silver_ventas_path = f"{base_abfss_path}/Tables/fct_ventas"
silver_compras_path = f"{base_abfss_path}/Tables/fct_compras"
silver_inventario_path = f"{base_abfss_path}/Tables/fct_inventario"

print("Iniciando Transformación de Capa Silver Controlada mediante Rutas ABFSS...")

# ==========================================
# DOMINIO: TRANSFORMACIÓN DE GASTOS
# ==========================================
try:
    print("-> Procesando Hechos de GASTOS...")
    df_bronze_gastos = spark.read.format("delta").load(bronze_gastos_path)

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
# DOMINIO: TRANSFORMACIÓN DE VENTAS (CALIBRADO)
# ==========================================
try:
    print("\n-> Procesando Hechos de VENTAS con esquema real...")
    df_bronze_ventas = spark.read.format("delta").load(bronze_ventas_path)

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
        F.col("Torre").cast(StringType()).alias("logistica_torre"),
        F.col("Apto").cast(StringType()).alias("logistica_apto"),
        F.col("Unidad").cast(StringType()).alias("logistica_unidad"),
        F.col("Observaciones").cast(StringType()).alias("observaciones"),
        F.col("Notas").cast(StringType()).alias("notas"),
        F.col("_nombre_pestaña").alias("origen_pestaña"),
        F.col("_fecha_ingestion").alias("fecha_ingestion_bronze"),
        F.current_timestamp().alias("fecha_procesado_silver")
    ).filter(F.col("fecha").isNotNull() | F.col("total_venta_cop").isNotNull())

    df_silver_ventas.write \
        .format("delta") \
        .mode("overwrite") \
        .option("overwriteSchema", "true") \
        .save(silver_ventas_path)

    print(f"   [Éxito] Datos de VENTAS guardados físicamente en OneLake Silver: {silver_ventas_path}")

except Exception as e:
    print(f"   [Error] Fallo al transformar VENTAS en Silver: {str(e)}")
    raise e

# ==========================================
# DOMINIO: TRANSFORMACIÓN DE COMPRAS (COMPRAS_INVENTARIO)
# Transacciones de compra/entrada de mercancía - un registro por compra
# ==========================================
try:
    print("\n-> Procesando Hechos de COMPRAS...")
    df_bronze_compras = spark.read.format("delta").load(bronze_compras_path)

    df_silver_compras = df_bronze_compras.select(
        F.col("Fecha").cast(DateType()).alias("fecha"),
        F.col("Código_producto").cast(StringType()).alias("codigo_producto"),
        F.col("Producto").cast(StringType()).alias("producto"),
        F.col("Categoría").cast(StringType()).alias("categoria_producto"),
        F.col("Proveedor").cast(StringType()).alias("proveedor"),
        F.col("Cantidad").cast(DoubleType()).alias("cantidad"),
        F.col("Costo_unitario_COP").cast(DoubleType()).alias("costo_unitario_cop"),
        F.col("Total_compra_COP").cast(DoubleType()).alias("total_compra_cop"),
        F.col("Estado_Disponible_Vendido").cast(StringType()).alias("estado_disponible_vendido"),
        # Nota: columna 'si' descartada intencionalmente - confirmado con el cliente que no es necesaria.
        F.col("Notas").cast(StringType()).alias("notas"),
        F.col("_nombre_pestaña").alias("origen_pestaña"),
        F.col("_fecha_ingestion").alias("fecha_ingestion_bronze"),
        F.current_timestamp().alias("fecha_procesado_silver")
    ).filter(F.col("fecha").isNotNull() | F.col("producto").isNotNull())

    df_silver_compras.write \
        .format("delta") \
        .mode("overwrite") \
        .option("overwriteSchema", "true") \
        .save(silver_compras_path)

    print(f"   [Éxito] Datos de COMPRAS guardados físicamente en OneLake Silver: {silver_compras_path}")

except Exception as e:
    print(f"   [Error] Fallo al transformar COMPRAS en Silver: {str(e)}")
    raise e

# ==========================================
# DOMINIO: TRANSFORMACIÓN DE INVENTARIO (INVENTARIO DEFINITIVO)
# Ledger maestro con saldo de stock por producto (ya calculado en origen)
# ==========================================
try:
    print("\n-> Procesando Hechos de INVENTARIO (INVENTARIO DEFINITIVO)...")
    df_bronze_inventario = spark.read.format("delta").load(bronze_inventario_definitivo_path)

    df_silver_inventario = df_bronze_inventario.select(
        F.col("Fecha_entrada_Salida").cast(DateType()).alias("fecha"),
        F.col("ID_interno").cast(StringType()).alias("id_interno"),
        F.col("Código_proveedores").cast(StringType()).alias("codigo_proveedor"),
        F.col("Barcode").cast(StringType()).alias("barcode"),
        F.col("Categoría").cast(StringType()).alias("categoria_producto"),
        F.col("Nombre_Producto").cast(StringType()).alias("nombre_producto"),
        F.col("Stock_inicial").cast(DoubleType()).alias("stock_inicial"),
        F.col("Entradas").cast(DoubleType()).alias("entradas"),
        F.col("Salidas").cast(DoubleType()).alias("salidas"),
        F.col("Stock_actual").cast(DoubleType()).alias("stock_actual"),
        F.col("Costo_unitario").cast(DoubleType()).alias("costo_unitario"),
        F.col("Costo_total_ENTRADAS").cast(DoubleType()).alias("costo_total_entradas"),
        F.col("Valor_total_Final").cast(DoubleType()).alias("valor_total_final"),
        F.col("Proveedor").cast(StringType()).alias("proveedor"),
        F.col("Concepto").cast(StringType()).alias("concepto"),
        F.col("Margen").cast(DoubleType()).alias("margen"),
        F.col("Precio_Venta").cast(DoubleType()).alias("precio_venta"),
        F.col("Precio_Final_VENTA").cast(DoubleType()).alias("precio_final_venta"),
        F.col("PRECIO_VENTA_NAVIDAD").cast(DoubleType()).alias("precio_venta_navidad"),
        F.col("Venta_Total_Salida").cast(DoubleType()).alias("venta_total_salida"),
        F.col("Venta_Proyectada").cast(DoubleType()).alias("venta_proyectada"),
        F.col("Ganancia_Unitaria_REAL").cast(DoubleType()).alias("ganancia_unitaria_real"),
        F.col("LOTE").cast(StringType()).alias("lote"),
        F.col("FECHA_FAB").cast(DateType()).alias("fecha_fabricacion"),
        F.col("FECHA_EXP").cast(DateType()).alias("fecha_expiracion"),
        F.col("RAPPI").cast(StringType()).alias("vendido_rappi"),
        F.col("Precio_Rappi").cast(DoubleType()).alias("precio_rappi"),
        # Nota: Unnamed:_27 y Unnamed:_30 son columnas fantasma de Excel, se descartan intencionalmente
        F.col("_nombre_pestaña").alias("origen_pestaña"),
        F.col("_fecha_ingestion").alias("fecha_ingestion_bronze"),
        F.current_timestamp().alias("fecha_procesado_silver")
    ).filter(F.col("fecha").isNotNull() | F.col("nombre_producto").isNotNull())

    # Validación de consistencia: stock_actual debería = stock_inicial + entradas - salidas
    df_silver_inventario = df_silver_inventario.withColumn(
        "stock_consistente",
        F.when(
            F.col("stock_actual") == (
                F.coalesce(F.col("stock_inicial"), F.lit(0.0)) +
                F.coalesce(F.col("entradas"), F.lit(0.0)) -
                F.coalesce(F.col("salidas"), F.lit(0.0))
            ),
            F.lit(True)
        ).otherwise(F.lit(False))
    )

    inconsistentes = df_silver_inventario.filter(F.col("stock_consistente") == False).count()
    if inconsistentes > 0:
        print(f"   [Aviso] {inconsistentes} filas con stock_actual inconsistente respecto a stock_inicial + entradas - salidas.")

    df_silver_inventario.write \
        .format("delta") \
        .mode("overwrite") \
        .option("overwriteSchema", "true") \
        .save(silver_inventario_path)

    print(f"   [Éxito] Datos de INVENTARIO guardados físicamente en OneLake Silver: {silver_inventario_path}")

except Exception as e:
    print(f"   [Error] Fallo al transformar INVENTARIO en Silver: {str(e)}")
    raise e

print("\n¡Capa Silver finalizada con éxito para GASTOS, VENTAS, COMPRAS e INVENTARIO!")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

df_inv = spark.read.format("delta").load(f"{base_abfss_path}/Tables/fct_inventario")
df_inv.filter(F.col("stock_consistente") == False).select(
    "id_interno", "nombre_producto", "stock_inicial", "entradas", "salidas", "stock_actual"
).show(truncate=False)


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

base_abfss_path = "abfss://b14581ac-9906-43e2-809c-c2fd4315ad5b@onelake.dfs.fabric.microsoft.com/abe92425-50d3-48f4-baa0-ebbfadd93f25"

df_compras = spark.read.format("delta").load(f"{base_abfss_path}/Tables/fct_compras")
df_inv = spark.read.format("delta").load(f"{base_abfss_path}/Tables/fct_inventario")

print("Códigos de producto en COMPRAS (muestra):")
df_compras.select("codigo_producto").distinct().show(10, truncate=False)

print("Barcodes / ID interno en INVENTARIO (muestra):")
df_inv.select("id_interno", "barcode").distinct().show(10, truncate=False)

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
