---
name: growme
description: |
  Estructuración del contexto y lógica de negocio previo al desarrollo.
  Utiliza un proceso de interrogación sistemático e interactivo para definir
  los requerimientos del negocio y generar/actualizar los archivos maestros
  `spec.md` (especificaciones funcionales y de negocio) y `decisions.md`
  (bitácora persistente de decisiones y arquitectura).
---

# Growme Skill: Levantamiento de Contexto y Lógica de Negocio

## Propósito
Antes de tocar cualquier línea de código o interfaz de usuario, la lógica de negocio y las reglas operativas deben estar claramente delimitadas. La skill `growme` conduce una sesión estructurada de definición de producto para generar dos documentos fundacionales en la raíz del proyecto:
1. `spec.md`: Especificaciones funcionales, requerimientos, casos de uso, flujos y entidades.
2. `decisions.md`: Registro estructurado de decisiones de diseño, arquitectura y negocio (ADRs).

---

## Cuándo activar esta skill
- Al iniciar una nueva funcionalidad, reporte, pipeline o módulo.
- Cuando el usuario indique frases como:
  - *"Usa growme para estructurar las especificaciones de mi proyecto"*
  - *"Inicia la sesión de growme para definir la lógica de negocio"*
  - *"Actualiza las especificaciones y decisiones con growme"*
- Cuando los requerimientos sean ambiguos o falte contexto de dominio antes de programar o transformar datos.

---

## Procedimiento Paso a Paso

### Paso 1: Verificación de Documentos Existentes
1. Verificar si existen `spec.md` y `decisions.md` en la raíz del workspace.
2. Si ya existen, leerlos para comprender el estado actual antes de plantear nuevas preguntas o modificaciones.

### Paso 2: Interrogatorio Sistemático
Conducir una conversación enfocada en el negocio, estructurada en los siguientes pilares (sin abrumar; preguntar de 2 a 3 temas clave por turno o usar opciones cuando aplique):
- **Objetivo y Problema**: ¿Qué problema de negocio resuelve esta funcionalidad? ¿Quién es el usuario o consumidor final?
- **Flujos de Usuario / Datos**: ¿Cuál es el recorrido paso a paso (happy path) y qué excepciones o casos borde existen?
- **Reglas de Negocio y Restricciones**: Reglas de cálculo, validaciones requeridas, monedas, impuestos, stocks, permisos, etc.
- **Entidades y Atributos**: Datos esenciales que deben capturarse, transformarse, almacenarse o sincronizarse.
- **Métricas de Éxito**: ¿Cómo sabemos que la solución cumple con el requerimiento operativo y analítico?

### Paso 3: Generación / Actualización de `spec.md`
Estructurar `spec.md` con la siguiente plantilla estandarizada:

```markdown
# Especificaciones de Aplicación: [Nombre del Módulo / Proyecto]

## 1. Resumen Ejecutivo y Objetivos
- **Problema de Negocio:**
- **Propuesta de Solución:**
- **Usuarios / Roles Involucrados:**

## 2. Requerimientos Funcionales
- **RF-01:** Descripción, entradas, procesamiento y salidas.
- **RF-02:** ...

## 3. Modelo de Dominio y Variables de Negocio
- **Entidades:** [Entidad, campos, tipos, reglas de validación]
- **Constantes y Políticas:** [Comisiones, límites, formatos, estados]

## 4. Flujos de Trabajo (Workflows)
1. **Flujo Principal (Happy Path):**
2. **Flujos Alternos y Manejo de Errores:**

## 5. Criterios de Aceptación
- [ ] Criterio 1
- [ ] Criterio 2
```

### Paso 4: Generación / Actualización de `decisions.md`
Registrar cada decisión clave tomada durante la sesión en formato ADR (Architecture/Business Decision Record):

```markdown
# Bitácora de Decisiones (Decisions Log)

## [ADR-00X] [Título de la Decisión]
- **Fecha:** YYYY-MM-DD
- **Estado:** [Aprobado / Propuesto / Superado]
- **Contexto:** ¿Qué problema o dilema motivó esta decisión?
- **Decisión Tomada:** ¿Qué camino o regla se adoptó y por qué?
- **Alternativas Consideradas:** Opciones descartadas y razón de descarte.
- **Consecuencias:** Impacto técnico, operativo o de mantenimiento.
```

### Paso 5: Confirmación con el Desarrollador
Presentar el resumen de `spec.md` y `decisions.md` al usuario para su aprobación final antes de invocar la fase de implementación o la skill `map-pokeout`.
