# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "5004f4fc-709d-4412-907f-fb8c21b64633",
# META       "default_lakehouse_name": "lh_gold_velykapet",
# META       "default_lakehouse_workspace_id": "b14581ac-9906-43e2-809c-c2fd4315ad5b",
# META       "known_lakehouses": [
# META         {
# META           "id": "787ca3da-cb1e-4bc7-bcec-04cb2415e5d4"
# META         },
# META         {
# META           "id": "5004f4fc-709d-4412-907f-fb8c21b64633"
# META         }
# META       ]
# META     }
# META   }
# META }

# CELL ********************

from pyspark.sql import functions as F
from pyspark.sql.types import IntegerType

# 1. Definición de Rutas ABFSS (Origen Silver y Destino Gold)
base_abfss_path = "abfss://b14581ac-9906-43e2-809c-c2fd4315ad5b@onelake.dfs.fabric.microsoft.com/abe92425-50d3-48f4-baa0-ebbfadd93f25"

silver_gastos_path = f"{base_abfss_path}/Tables/fct_gastos"
silver_ventas_path = f"{base_abfss_path}/Tables/fct_ventas"

# Destinos en Gold
gold_dim_calendario_path = f"{base_abfss_path}/Tables/dim_calendario"
gold_dim_pago_path = f"{base_abfss_path}/Tables/dim_metodo_pago"
gold_fct_gastos_path = f"{base_abfss_path}/Tables/gold_fct_gastos"
gold_fct_ventas_path = f"{base_abfss_path}/Tables/gold_fct_ventas"

print("Iniciando Construcción de la Capa Gold Estable...")

try:
    # 2. Leer datos controlados de Silver
    df_silver_gastos = spark.read.format("delta").load(silver_gastos_path)
    df_silver_ventas = spark.read.format("delta").load(silver_ventas_path)
    
    # ==========================================
    # CONSTRUCCIÓN DE DIM_CALENDARIO (Dimensión Compartida)
    # ==========================================
    print("-> Creando dim_calendario unificada...")
    # Extraer todas las fechas únicas de ambos universos para que no falte ningún día
    fechas_gastos = df_silver_gastos.select("fecha").distinct()
    fechas_ventas = df_silver_ventas.select("fecha").distinct()
    
    df_fechas = fechas_gastos.union(fechas_ventas).distinct().filter(F.col("fecha").isNotNull())
    
    # Enriquecer la dimensión temporal para Power BI
    df_dim_calendario = df_fechas.select(
        F.col("fecha").alias("fecha_key"),
        F.year("fecha").alias("anio"),
        F.month("fecha").alias("mes_nro"),
        F.date_format("fecha", "MMMM").alias("mes_nombre"),
        F.dayofmonth("fecha").alias("dia"),
        F.date_format("fecha", "EEEE").alias("dia_semana_nombre"),
        F.quarter("fecha").alias("trimestre")
    )
    
    df_dim_calendario.write.format("delta").mode("overwrite").option("overwriteSchema", "true").save(gold_dim_calendario_path)
    print("   [Éxito] dim_calendario guardada en Gold.")

    # ==========================================
    # CONSTRUCCIÓN DE DIM_METODO_PAGO
    # ==========================================
    print("-> Creando dim_metodo_pago...")
    pagos_gastos = df_silver_gastos.select(F.coalesce(F.col("metodo_pago"), F.lit("NO ESPECIFICADO")).alias("metodo_pago")).distinct()
    pagos_ventas = df_silver_ventas.select(F.coalesce(F.col("metodo_pago"), F.lit("NO ESPECIFICADO")).alias("metodo_pago")).distinct()
    
    df_pagos = pagos_gastos.union(pagos_ventas).distinct()
    
    # Añadir un ID subrogado (Surrogate Key) numérico limpio
    df_dim_pago = df_pagos.withColumn("metodo_pago_sk", F.monotonically_increasing_id().cast(IntegerType())) \
                          .select("metodo_pago_sk", "metodo_pago")
                          
    df_dim_pago.write.format("delta").mode("overwrite").option("overwriteSchema", "true").save(gold_dim_pago_path)
    print("   [Éxito] dim_metodo_pago guardada en Gold.")

    # ==========================================
    # PREPARACIÓN DE HECHOS FINALES (Unión con llaves subrogadas)
    # ==========================================
    print("-> Vinculando hechos finales Gold con dimensiones...")
    
    # Gastos Gold
    gold_fct_gastos = df_silver_gastos.join(df_dim_pago, df_silver_gastos.metodo_pago == df_dim_pago.metodo_pago, "left") \
        .select(
            F.col("fecha").alias("fecha_key"),
            F.col("metodo_pago_sk"),
            F.col("descripcion"),
            F.col("categoria_gasto"),
            F.col("monto_cop"),
            F.col("notas"),
            F.col("origen_pestaña")
        )
    gold_fct_gastos.write.format("delta").mode("overwrite").option("overwriteSchema", "true").save(gold_fct_gastos_path)
    
    # Ventas Gold
    gold_fct_ventas = df_silver_ventas.join(df_dim_pago, df_silver_ventas.metodo_pago == df_dim_pago.metodo_pago, "left") \
        .select(
            F.col("fecha").alias("fecha_key"),
            F.col("metodo_pago_sk"),
            F.col("anio"),
            F.col("codigo_producto"),
            F.col("producto"),
            F.col("categoria_producto"),
            F.col("cantidad"),
            F.col("precio_unitario_cop"),
            F.col("total_venta_cop"),
            F.col("costo_unitario_cop"),
            F.col("costo_total_cop"),
            F.col("utilidad_cop"),
            F.col("canal_venta"),
            F.col("codigo_transaccion"),
            F.col("logistica_torre"),
            F.col("logistica_apto"),
            F.col("logistica_unidad"),
            F.col("origen_pestaña")
        )
    gold_fct_ventas.write.format("delta").mode("overwrite").option("overwriteSchema", "true").save(gold_fct_ventas_path)
    
    print("   [Éxito] Tablas de hechos Gold vinculadas y listas.")
    print("\n¡Capa Gold finalizada con éxito! Tu modelo estrella está listo en OneLake.")

except Exception as e:
    print(f"   [Error] Fallo en la capa Gold: {str(e)}")
    raise e


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

from delta.tables import DeltaTable

base_abfss_path = "abfss://b14581ac-9906-43e2-809c-c2fd4315ad5b@onelake.dfs.fabric.microsoft.com/abe92425-50d3-48f4-baa0-ebbfadd93f25"

print("Registrando tablas en el catálogo visual de Fabric...")

tables = {
    "fct_gastos":      f"{base_abfss_path}/Tables/fct_gastos",
    "fct_ventas":      f"{base_abfss_path}/Tables/fct_ventas",
    "dim_calendario":  f"{base_abfss_path}/Tables/dim_calendario",
    "dim_metodo_pago": f"{base_abfss_path}/Tables/dim_metodo_pago",
    "gold_fct_gastos": f"{base_abfss_path}/Tables/gold_fct_gastos",
    "gold_fct_ventas": f"{base_abfss_path}/Tables/gold_fct_ventas",
}

for table_name, location in tables.items():
    if spark.catalog.tableExists(table_name):
        # Table already registered — refresh metadata to pick up schema changes
        spark.sql(f"REFRESH TABLE {table_name}")
        print(f"   [Refrescada] {table_name}")
    else:
        # First run — register it
        spark.catalog.createTable(table_name, location, source="delta")
        print(f"   [Registrada] {table_name}")

print("\n¡Registro completado con éxito!")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

print("Verificando tablas registradas en el catálogo...\n")

expected = [
    "fct_gastos", "fct_ventas",
    "dim_calendario", "dim_metodo_pago",
    "gold_fct_gastos", "gold_fct_ventas"
]

all_ok = True
for t in expected:
    exists = spark.catalog.tableExists(t)
    status = "[OK]" if exists else "[FALTA]"
    if not exists:
        all_ok = False
    count = spark.table(t).count() if exists else 0
    print(f"   {status} {t} — {count:,} filas")

print()
if all_ok:
    print("¡Todas las tablas están disponibles y listas para el modelo semántico!")
else:
    raise Exception("Faltan tablas en el catálogo. Revisar celdas anteriores.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# 1. Definir la ruta base que estamos utilizando
base_abfss_path = "abfss://b14581ac-9906-43e2-809c-c2fd4315ad5b@onelake.dfs.fabric.microsoft.com/abe92425-50d3-48f4-baa0-ebbfadd93f25"

print("Registrando tablas en el catálogo visual de Fabric...")

# 2. Registrar las tablas de la capa Silver
spark.sql(f"CREATE TABLE IF NOT EXISTS fct_gastos USING DELTA LOCATION '{base_abfss_path}/Tables/fct_gastos'")
spark.sql(f"CREATE TABLE IF NOT EXISTS fct_ventas USING DELTA LOCATION '{base_abfss_path}/Tables/fct_ventas'")

# 3. Registrar las tablas de la capa Gold (Modelo Estrella)
spark.sql(f"CREATE TABLE IF NOT EXISTS dim_calendario USING DELTA LOCATION '{base_abfss_path}/Tables/dim_calendario'")
spark.sql(f"CREATE TABLE IF NOT EXISTS dim_metodo_pago USING DELTA LOCATION '{base_abfss_path}/Tables/dim_metodo_pago'")
spark.sql(f"CREATE TABLE IF NOT EXISTS gold_fct_gastos USING DELTA LOCATION '{base_abfss_path}/Tables/gold_fct_gastos'")
spark.sql(f"CREATE TABLE IF NOT EXISTS gold_fct_ventas USING DELTA LOCATION '{base_abfss_path}/Tables/gold_fct_ventas'")

print("¡Registro completado con éxito!")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark",
# META   "frozen": true,
# META   "editable": false
# META }

# CELL ********************

# Definición de tu ruta ABFSS base ya validada
base_abfss_path = "abfss://b14581ac-9906-43e2-809c-c2fd4315ad5b@onelake.dfs.fabric.microsoft.com/abe92425-50d3-48f4-baa0-ebbfadd93f25"

print("Iniciando registro directo en el catálogo de Fabric mediante API...")

# 1. Registrar las tablas en la capa Silver
spark.catalog.createTable("fct_gastos", f"{base_abfss_path}/Tables/fct_gastos", source="delta")
spark.catalog.createTable("fct_ventas", f"{base_abfss_path}/Tables/fct_ventas", source="delta")
print("-> Capa Silver registrada en el catálogo.")

# 2. Registrar las tablas en la capa Gold
spark.catalog.createTable("dim_calendario", f"{base_abfss_path}/Tables/dim_calendario", source="delta")
spark.catalog.createTable("dim_metodo_pago", f"{base_abfss_path}/Tables/dim_metodo_pago", source="delta")
spark.catalog.createTable("gold_fct_gastos", f"{base_abfss_path}/Tables/gold_fct_gastos", source="delta")
spark.catalog.createTable("gold_fct_ventas", f"{base_abfss_path}/Tables/gold_fct_ventas", source="delta")
print("-> Capa Gold (Modelo Estrella) registrada en el catálogo.")

print("\n¡[ÉXITO] Todas las tablas han sido enlazadas al catálogo visual!")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark",
# META   "frozen": true,
# META   "editable": false
# META }

# CELL ********************

base_abfss_path = "abfss://b14581ac-9906-43e2-809c-c2fd4315ad5b@onelake.dfs.fabric.microsoft.com/abe92425-50d3-48f4-baa0-ebbfadd93f25"
spark.catalog.createTable("dim_calendario", f"{base_abfss_path}/Tables/dim_calendario", source="delta")
spark.catalog.createTable("dim_metodo_pago", f"{base_abfss_path}/Tables/dim_metodo_pago", source="delta")
spark.catalog.createTable("gold_fct_gastos", f"{base_abfss_path}/Tables/gold_fct_gastos", source="delta")
spark.catalog.createTable("gold_fct_ventas", f"{base_abfss_path}/Tables/gold_fct_ventas", source="delta")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark",
# META   "frozen": true,
# META   "editable": false
# META }

# CELL ********************

from pyspark.sql import functions as F
from pyspark.sql.types import IntegerType

# Definición de Rutas ABFSS (Origen Silver y Destino Gold)
base_abfss_path = "abfss://b14581ac-9906-43e2-809c-c2fd4315ad5b@onelake.dfs.fabric.microsoft.com/abe92425-50d3-48f4-baa0-ebbfadd93f25"

silver_gastos_path = f"{base_abfss_path}/Tables/fct_gastos"
silver_ventas_path = f"{base_abfss_path}/Tables/fct_ventas"
silver_compras_path = f"{base_abfss_path}/Tables/fct_compras"
silver_inventario_path = f"{base_abfss_path}/Tables/fct_inventario"

# Destinos en Gold
gold_dim_calendario_path  = f"{base_abfss_path}/Tables/dim_calendario"
gold_dim_pago_path        = f"{base_abfss_path}/Tables/dim_metodo_pago"
gold_dim_producto_path    = f"{base_abfss_path}/Tables/dim_producto"
gold_fct_gastos_path      = f"{base_abfss_path}/Tables/gold_fct_gastos"
gold_fct_ventas_path      = f"{base_abfss_path}/Tables/gold_fct_ventas"
gold_fct_compras_path     = f"{base_abfss_path}/Tables/gold_fct_compras"
gold_fct_inventario_path  = f"{base_abfss_path}/Tables/gold_fct_inventario"

print("Iniciando Construcción de la Capa Gold Estable...")

try:
    # Leer datos controlados de Silver
    df_silver_gastos     = spark.read.format("delta").load(silver_gastos_path)
    df_silver_ventas     = spark.read.format("delta").load(silver_ventas_path)
    df_silver_compras    = spark.read.format("delta").load(silver_compras_path)
    df_silver_inventario = spark.read.format("delta").load(silver_inventario_path)

    # ==========================================
    # CONSTRUCCIÓN DE DIM_CALENDARIO (Dimensión Compartida)
    # Ahora incluye fechas de los cuatro dominios para que ningún día falte
    # ==========================================
    print("-> Creando dim_calendario unificada...")
    fechas_gastos     = df_silver_gastos.select("fecha")
    fechas_ventas     = df_silver_ventas.select("fecha")
    fechas_compras    = df_silver_compras.select("fecha")
    fechas_inventario = df_silver_inventario.select("fecha")

    df_fechas = fechas_gastos.union(fechas_ventas) \
        .union(fechas_compras) \
        .union(fechas_inventario) \
        .distinct() \
        .filter(F.col("fecha").isNotNull())

    df_dim_calendario = df_fechas.select(
        F.col("fecha").alias("fecha_key"),
        F.year("fecha").alias("anio"),
        F.month("fecha").alias("mes_nro"),
        F.date_format("fecha", "MMMM").alias("mes_nombre"),
        F.dayofmonth("fecha").alias("dia"),
        F.date_format("fecha", "EEEE").alias("dia_semana_nombre"),
        F.quarter("fecha").alias("trimestre")
    )

    df_dim_calendario.write.format("delta").mode("overwrite").option("overwriteSchema", "true").save(gold_dim_calendario_path)
    print("   [Éxito] dim_calendario guardada en Gold.")

    # ==========================================
    # CONSTRUCCIÓN DE DIM_METODO_PAGO
    # ==========================================
    print("-> Creando dim_metodo_pago...")
    pagos_gastos = df_silver_gastos.select(F.coalesce(F.col("metodo_pago"), F.lit("NO ESPECIFICADO")).alias("metodo_pago")).distinct()
    pagos_ventas = df_silver_ventas.select(F.coalesce(F.col("metodo_pago"), F.lit("NO ESPECIFICADO")).alias("metodo_pago")).distinct()

    df_pagos = pagos_gastos.union(pagos_ventas).distinct()

    df_dim_pago = df_pagos.withColumn("metodo_pago_sk", F.monotonically_increasing_id().cast(IntegerType())) \
                          .select("metodo_pago_sk", "metodo_pago")

    df_dim_pago.write.format("delta").mode("overwrite").option("overwriteSchema", "true").save(gold_dim_pago_path)
    print("   [Éxito] dim_metodo_pago guardada en Gold.")

    # ==========================================
    # CONSTRUCCIÓN DE DIM_PRODUCTO (Dimensión Compartida)
    # Clave natural: codigo_producto (ventas/compras) = id_interno (inventario)
    # IMPORTANTE: barcode NO es clave -- varios productos pueden compartir el mismo
    # barcode de empaque físico, por lo que solo se conserva como atributo descriptivo.
    # ==========================================
    print("-> Creando dim_producto unificada...")

    productos_ventas = df_silver_ventas.select(
        F.col("codigo_producto"),
        F.col("producto").alias("nombre_producto"),
        F.col("categoria_producto")
    )

    productos_compras = df_silver_compras.select(
        F.col("codigo_producto"),
        F.col("producto").alias("nombre_producto"),
        F.col("categoria_producto")
    )

    productos_inventario = df_silver_inventario.select(
        F.col("id_interno").alias("codigo_producto"),
        F.col("nombre_producto"),
        F.col("categoria_producto"),
        F.col("barcode")
    )

    df_productos = productos_ventas.unionByName(productos_compras, allowMissingColumns=True) \
        .unionByName(productos_inventario, allowMissingColumns=True) \
        .filter(F.col("codigo_producto").isNotNull())

    # Consolidar duplicados: un mismo codigo_producto puede aparecer en varias fuentes
    df_productos_consolidado = df_productos.groupBy("codigo_producto").agg(
        F.first("nombre_producto", ignorenulls=True).alias("nombre_producto"),
        F.first("categoria_producto", ignorenulls=True).alias("categoria_producto"),
        F.first("barcode", ignorenulls=True).alias("barcode")
    )

    df_dim_producto = df_productos_consolidado.withColumn(
        "producto_sk", F.monotonically_increasing_id().cast(IntegerType())
    ).select("producto_sk", "codigo_producto", "nombre_producto", "categoria_producto", "barcode")

    df_dim_producto.write.format("delta").mode("overwrite").option("overwriteSchema", "true").save(gold_dim_producto_path)
    print(f"   [Éxito] dim_producto guardada en Gold ({df_dim_producto.count():,} productos).")

    # ==========================================
    # PREPARACIÓN DE HECHOS FINALES (Unión con llaves subrogadas)
    # ==========================================
    print("-> Vinculando hechos finales Gold con dimensiones...")

    # Alias explícito de cada DataFrame para evitar ambigüedad de columnas en los joins
    g  = df_silver_gastos.alias("g")
    v  = df_silver_ventas.alias("v")
    c  = df_silver_compras.alias("c")
    i  = df_silver_inventario.alias("i")
    p  = df_dim_pago.alias("p")
    pr = df_dim_producto.alias("pr")

    # Gastos Gold
    gold_fct_gastos = g.join(p, F.col("g.metodo_pago") == F.col("p.metodo_pago"), "left") \
        .select(
            F.col("g.fecha").alias("fecha_key"),
            F.col("p.metodo_pago_sk"),
            F.col("g.descripcion"),
            F.col("g.categoria_gasto"),
            F.col("g.monto_cop"),
            F.col("g.notas"),
            F.col("g.origen_pestaña")
        )
    gold_fct_gastos.write.format("delta").mode("overwrite").option("overwriteSchema", "true").save(gold_fct_gastos_path)

    # Ventas Gold (ahora también vinculado a dim_producto)
    gold_fct_ventas = v.join(p, F.col("v.metodo_pago") == F.col("p.metodo_pago"), "left") \
        .join(pr, F.col("v.codigo_producto") == F.col("pr.codigo_producto"), "left") \
        .select(
            F.col("v.fecha").alias("fecha_key"),
            F.col("p.metodo_pago_sk"),
            F.col("pr.producto_sk"),
            F.col("v.anio"),
            F.col("v.codigo_producto"),
            F.col("v.cantidad"),
            F.col("v.precio_unitario_cop"),
            F.col("v.total_venta_cop"),
            F.col("v.costo_unitario_cop"),
            F.col("v.costo_total_cop"),
            F.col("v.utilidad_cop"),
            F.col("v.canal_venta"),
            F.col("v.codigo_transaccion"),
            F.col("v.logistica_torre"),
            F.col("v.logistica_apto"),
            F.col("v.logistica_unidad"),
            F.col("v.origen_pestaña")
        )
    gold_fct_ventas.write.format("delta").mode("overwrite").option("overwriteSchema", "true").save(gold_fct_ventas_path)

    # Compras Gold
    gold_fct_compras = c.join(pr, F.col("c.codigo_producto") == F.col("pr.codigo_producto"), "left") \
        .select(
            F.col("c.fecha").alias("fecha_key"),
            F.col("pr.producto_sk"),
            F.col("c.codigo_producto"),
            F.col("c.proveedor"),
            F.col("c.cantidad"),
            F.col("c.costo_unitario_cop"),
            F.col("c.total_compra_cop"),
            F.col("c.estado_disponible_vendido"),
            F.col("c.notas"),
            F.col("c.origen_pestaña")
        )
    gold_fct_compras.write.format("delta").mode("overwrite").option("overwriteSchema", "true").save(gold_fct_compras_path)

    # Inventario Gold
    gold_fct_inventario = i.join(pr, F.col("i.id_interno") == F.col("pr.codigo_producto"), "left") \
        .select(
            F.col("i.fecha").alias("fecha_key"),
            F.col("pr.producto_sk"),
            F.col("i.id_interno"),
            F.col("i.proveedor"),
            F.col("i.concepto"),
            F.col("i.stock_inicial"),
            F.col("i.entradas"),
            F.col("i.salidas"),
            F.col("i.stock_actual"),
            F.col("i.stock_consistente"),
            F.col("i.costo_unitario"),
            F.col("i.costo_total_entradas"),
            F.col("i.valor_total_final"),
            F.col("i.margen"),
            F.col("i.precio_venta"),
            F.col("i.precio_final_venta"),
            F.col("i.precio_venta_navidad"),
            F.col("i.venta_total_salida"),
            F.col("i.venta_proyectada"),
            F.col("i.ganancia_unitaria_real"),
            F.col("i.lote"),
            F.col("i.fecha_fabricacion"),
            F.col("i.fecha_expiracion"),
            F.col("i.vendido_rappi"),
            F.col("i.precio_rappi"),
            F.col("i.origen_pestaña")
        )
    gold_fct_inventario.write.format("delta").mode("overwrite").option("overwriteSchema", "true").save(gold_fct_inventario_path)

    print("   [Éxito] Tablas de hechos Gold vinculadas y listas.")
    print("\n¡Capa Gold finalizada con éxito! Tu modelo estrella (con inventario) está listo en OneLake.")

except Exception as e:
    print(f"   [Error] Fallo en la capa Gold: {str(e)}")
    raise e

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

base_abfss_path = "abfss://b14581ac-9906-43e2-809c-c2fd4315ad5b@onelake.dfs.fabric.microsoft.com/abe92425-50d3-48f4-baa0-ebbfadd93f25"

print("Registrando tablas en el catálogo visual de Fabric...")

tables = {
    # Silver
    "fct_gastos":      f"{base_abfss_path}/Tables/fct_gastos",
    "fct_ventas":      f"{base_abfss_path}/Tables/fct_ventas",
    "fct_compras":     f"{base_abfss_path}/Tables/fct_compras",
    "fct_inventario":  f"{base_abfss_path}/Tables/fct_inventario",
    # Gold - dimensiones
    "dim_calendario":  f"{base_abfss_path}/Tables/dim_calendario",
    "dim_metodo_pago": f"{base_abfss_path}/Tables/dim_metodo_pago",
    "dim_producto":    f"{base_abfss_path}/Tables/dim_producto",
    # Gold - hechos
    "gold_fct_gastos":     f"{base_abfss_path}/Tables/gold_fct_gastos",
    "gold_fct_ventas":     f"{base_abfss_path}/Tables/gold_fct_ventas",
    "gold_fct_compras":    f"{base_abfss_path}/Tables/gold_fct_compras",
    "gold_fct_inventario": f"{base_abfss_path}/Tables/gold_fct_inventario",
}

for table_name, location in tables.items():
    if spark.catalog.tableExists(table_name):
        # Tabla ya registrada — refrescar metadatos para tomar cambios de esquema
        spark.sql(f"REFRESH TABLE {table_name}")
        print(f"   [Refrescada] {table_name}")
    else:
        # Primera vez — registrarla
        spark.catalog.createTable(table_name, location, source="delta")
        print(f"   [Registrada] {table_name}")

print("\n¡Registro completado con éxito!")

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
