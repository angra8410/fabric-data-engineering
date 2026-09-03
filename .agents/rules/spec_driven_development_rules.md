# Reglas de Desarrollo Guiado por Especificaciones (Spec-Driven Development)

## 1. Principio Fundamental: Especificación Antes de Código
- Ninguna regla de negocio, fórmula de cálculo, métrica analítica o flujo de usuario debe implementarse directamente en el código o modelos sin estar registrada previamente en `spec.md`.
- Toda decisión técnica, arquitectónica o de modelado que altere el rumbo del proyecto debe documentarse en `decisions.md` mediante un Architecture Decision Record (ADR).

## 2. Flujo Operativo Obligatorio
1. **Fase de Contexto y Negocio (`growme`):**
   - Interrogar sistemáticamente los requerimientos antes de tocar scripts, modelos semánticos (TMDL), pipelines o interfaces.
   - Definir objetivos, entidades, fórmulas, flujos y criterios de aceptación en `spec.md`.
   - Registrar supuestos, tecnologías y alternativas descartadas en `decisions.md`.

2. **Fase de Fusión e Implementación (`map-pokeout`):**
   - Leer `spec.md` y `decisions.md` para extraer variables, constantes y reglas.
   - Mapear cada elemento hacia su correspondiente componente técnico (Notebooks PySpark, medidas DAX en Semantic Models, visuals PBIR, APIs o vistas).
   - Realizar ediciones quirúrgicas y trazables preservando convenciones de nombres y arquitectura preexistente.

## 3. Integridad y Coherencia de Datos
- Las métricas analíticas calculadas en reportes (Power BI / PBIR) deben ser coherentes con las definiciones de las capas Silver y Gold en Lakehouse.
- Mantener los criterios de aceptación actualizados con checks (`[x]`) a medida que se verifique cada entrega.
