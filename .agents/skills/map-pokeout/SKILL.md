---
name: map-pokeout
description: |
  Fusión de código guiada por especificaciones (Spec-Driven Development / SDD).
  Lee obligatoriamente los archivos maestros `spec.md` y `decisions.md` para mapear,
  inyectar y fusionar las variables, reglas y flujos de negocio directamente en la
  base de código e interfaces existentes del proyecto.
---

# Map-Pokeout Skill: Fusión de Código Guiada por Especificaciones

## Propósito
`map-pokeout` realiza la integración y desarrollo guiado por especificaciones (Spec-Driven Development). Su función primordial es tomar la definición de negocio acordada previamente en `spec.md` y las decisiones en `decisions.md`, y plasmarlas quirúrgicamente en el código fuente (frontend, backend, rutas API, reportes o modelos de datos) sin alterar la coherencia de la arquitectura preexistente.

---

## Cuándo activar esta skill
- Cuando el desarrollador solicite:
  - *"Usa map-pokeout para mapear spec.md en nuestra interfaz actual"*
  - *"Aplica map-pokeout para integrar los requerimientos"*
  - *"Fusiona el modelo de negocio con la base de código usando map-pokeout"*
- Al pasar de la fase de diseño/especificación a la fase de implementación de código.

---

## Procedimiento Paso a Paso

### Paso 1: Carga y Validación del Contexto Maestro
1. **Lectura Obligatoria de Archivos:**
   - Leer `spec.md`: Analizar las entidades, requerimientos funcionales (RF) y variables de negocio.
   - Leer `decisions.md`: Revisar las restricciones y decisiones arquitectónicas adoptadas para evitar regresiones.
   - Revisar reglas activas en `.agents/rules/` si existen.
2. Si alguno de los archivos maestros falta o no está completo, advertir al usuario y sugerir ejecutar la skill `growme` primero.

### Paso 2: Análisis de la Base de Código Existente
1. Localizar los archivos de código fuente relevantes para el cambio:
   - Componentes de interfaz (ej. reportes, dashboards, vistas o plantillas web).
   - Scripts, pipelines o transformaciones de datos (ej. Python, PySpark, notebooks, TMDL, DAX).
   - Rutas, controladores de servidor o esquemas de datos.
2. Identificar puntos de anclaje (hook points) para variables de negocio, estados y métricas.

### Paso 3: Plan de Mapeo (Spec-to-Code Mapping)
Elaborar una matriz de correspondencia mental o explícita:
- **Variable de Negocio / Entidad** ➔ **Propiedad en State / Modelo / Tabla de Datos**
- **Regla de Negocio / Validación** ➔ **Función de validación / Medida DAX / Regla de transformación**
- **Flujo de Usuario** ➔ **Controlador de UI / Visual interactivo / Handler de Eventos**
- **Criterio de Aceptación** ➔ **Prueba o verificación de resultados**

### Paso 4: Fusión Quirúrgica del Código
1. Aplicar los cambios con herramientas de edición precisas (`replace_file_content` o `multi_replace_file_content`).
2. Respetar las convenciones estilísticas y arquitectónicas ya presentes en el proyecto (no sobreescribir archivos enteros innecesariamente).
3. Mantener tipado, comentarios explicativos y trazabilidad hacia `spec.md` (ej. `// Implements RF-02 from spec.md`).

### Paso 5: Verificación y Actualización de Estado
1. Ejecutar verificaciones automáticas de sintaxis, compilación o pruebas si están configuradas en el proyecto.
2. Marcar en `spec.md` los criterios de aceptación completados (`[x]`).
3. Informar al desarrollador sobre los archivos modificados, los flujos integrados y los pasos siguientes para validación en ejecución.
