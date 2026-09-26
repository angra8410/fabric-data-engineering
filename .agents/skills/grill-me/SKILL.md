---
name: grill-me
description: |
  Entrevista interactiva rigurosa de diseño, arquitectura y validación técnica (Grill-Me).
  Interroga al desarrollador con preguntas críticas, desafiando supuestos, límites de escala,
  casos borde, costos y decisiones de diseño antes de pasar a la implementación.
---

# Grill-Me Skill: Entrevista Rigurosa de Arquitectura y Diseño Técnico

## Propósito
`grill-me` es una técnica de interrogación profunda utilizada por arquitectos y líderes técnicos senior para someter a prueba de estrés cualquier solución técnica, consulta SQL, pipeline de datos, modelo semántico o arquitectura antes de escribir código en producción. Su objetivo es detectar debilidades tempranas, evitar retrabajos costosos y asegurar que el desarrollador domine el "por qué" de cada decisión técnica.

---

## Cuándo activar esta skill
- Cuando el usuario invoque el comando `/grill-me` o pida expresamente ser interrogado con rigurosidad.
- Antes de aprobar un plan de implementación crítico o cambios arquitectónicos mayores.
- Cuando una solución parezca funcionar superficialmente pero oculte problemas de escalabilidad, concurrencia, costos o fallos en casos borde.
- Para preparación de entrevistas técnicas de nivel Senior / Staff / Architect.

---

## Procedimiento Paso a Paso

### Paso 1: Identificación del Dominio y Supuestos
1. Analizar el problema planteado, el esquema de datos y los requerimientos funcionales y no funcionales.
2. Identificar los supuestos implícitos que el desarrollador está asumiendo (ej. "los datos siempre vienen limpios", "el volumen no superará 100K filas", "los joins siempre tienen correspondencia 1:1", etc.).

### Paso 2: El Interrogatorio Crítico (Grilling)
Conducir una ronda de preguntas desafiantes, focalizadas e incisivas (1 o 2 preguntas por turno para mantener el diálogo ágil y enfocado). Evaluar:
- **Casos Borde y Datos Sucios:** ¿Qué sucede si los campos clave vienen con `NULL`, duplicados, caracteres especiales o desalineación horaria?
- **Escala y Rendimiento:** ¿Cómo se comporta la solución con 10M, 100M o 1B de filas? ¿Genera cuellos de botella en memoria (spill to disk), congestión de red o scans completos de tabla?
- **SARGabilidad y Planes de Ejecución:** ¿Se están usando predicados indexables o funciones envolventes que anulan el optimizador?
- **Arquitectura y Costos:** ¿La solución respeta la arquitectura Medallion? ¿Genera sobrecostos de capacidad en Fabric o computación innecesaria?
- **Concurrencia y Consistencia:** ¿Se contemplan transacciones concurrentes, bloqueos, o escrituras simultáneas en Delta Lake?

### Paso 3: Análisis de Respuestas y Contra-Argumentación
- No aceptar respuestas vagas como "lo indexamos" o "hacemos un filtro".
- Exigir la justificación técnica exacta (ej. tipo de join, particionamiento, comportamiento del Storage Engine vs Formula Engine en DAX).
- Señalar de inmediato los puntos ciegos técnicos y guiar al desarrollador hacia la solución óptima.

### Paso 4: Síntesis de Acuerdos
Una vez superada la prueba de estrés:
1. Resumir las decisiones clave acordadas.
2. Registrar o actualizar las especificaciones en `spec.md` y las decisiones arquitectónicas en `decisions.md` (formato ADR).
3. Habilitar el paso a la fase de implementación con garantía de solidez técnica.
