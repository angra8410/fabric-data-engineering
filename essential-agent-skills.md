# Essential Agent Skills: growme & map-pokeout

Guía integral para la configuración, despliegue y uso de las habilidades de agente (`growme` y `map-pokeout`) en el flujo de trabajo de desarrollo guiado por especificaciones (Spec-Driven Development).

---

## 1. Flujo de Trabajo Git en Nueva Rama

Para trabajar de forma segura y aislar la configuración de reglas y habilidades de agentes, se ejecuta el siguiente flujo desde la terminal:

```bash
# 1. Asegurar sincronización con la rama principal
git checkout main
git pull origin main

# 2. Crear y cambiar a la rama de características para las habilidades
git checkout -b feature/setup-agent-skills
```

---

## 2. Estructura de Directorios de Habilidades

La raíz de personalizaciones de agente del proyecto se encuentra en `.agents`. La estructura creada es:

```text
.agents/
├── mcp_config.json
└── skills/
    ├── growme/
    │   └── SKILL.md
    └── map-pokeout/
        └── SKILL.md
```

---

## 3. Definición Completa de Archivos SKILL.md

### 📂 `.agents/skills/growme/SKILL.md`
> **Propósito:** Interrogatorio interactivo para definir la lógica de negocio y generar los archivos maestros `spec.md` y `decisions.md`.

```markdown
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
Antes de tocar cualquier línea de código o interfaz de usuario, la lógica de negocio y las reglas operativas deben estar claramente delimitadas. La skill growme conduce una sesión estructurada de definición de producto para generar dos documentos fundacionales en la raíz del proyecto:
1. spec.md: Especificaciones funcionales, requerimientos, casos de uso, flujos y entidades.
2. decisions.md: Registro estructurado de decisiones de diseño, arquitectura y negocio (ADRs).

## Procedimiento Paso a Paso
1. **Verificación**: Comprobar si existen `spec.md` y `decisions.md` en el proyecto.
2. **Interrogatorio Sistemático**: Preguntas guiadas sobre objetivo, flujos, reglas, entidades y métricas.
3. **Generación de spec.md**: Estructuración del documento maestro de requerimientos.
4. **Generación de decisions.md**: Registro de ADRs con contexto, decisión y consecuencias.
5. **Aprobación**: Validación del usuario antes de pasar a la fase de código.
```

---

### 📂 `.agents/skills/map-pokeout/SKILL.md`
> **Propósito:** Desarrollo guiado por especificaciones (Spec-Driven Development) fusionando variables de negocio de `spec.md` y `decisions.md` en el código existente.

```markdown
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
map-pokeout realiza la integración y desarrollo guiado por especificaciones. Toma la definición acordada en spec.md y decisions.md y las plasma quirúrgicamente en el código fuente respetando la arquitectura preexistente.

## Procedimiento Paso a Paso
1. **Carga de Contexto**: Lectura obligatoria de `spec.md`, `decisions.md` y reglas activas.
2. **Análisis del Código**: Inspección de componentes, pipelines o interfaces existentes y puntos de anclaje.
3. **Mapeo (Spec-to-Code)**: Matriz de correspondencia entidad ➔ modelo/tabla, regla ➔ validador/cálculo, flujo ➔ interfaz/pipeline.
4. **Fusión Quirúrgica**: Modificación precisa preservando convenciones existentes.
5. **Verificación**: Validación de sintaxis, pruebas y actualización del progreso en `spec.md`.
```

---

## 4. Comandos de Activación en Terminal

Una vez integradas las skills en la rama, puedes interactuar directamente con tu agente usando los siguientes comandos:

| Objetivo | Comando sugerido |
| :--- | :--- |
| **Definir Lógica de Negocio** | `"Usa growme para estructurar las especificaciones de mi proyecto"` |
| **Mapear en Interfaz / Código** | `"Usa map-pokeout para mapear spec.md en nuestra interfaz actual"` |
| **Actualizar Decisiones** | `"Actualiza decisions.md usando growme con la última reunión de arquitectura"` |
| **Implementar Nuevo Flujo** | `"Aplica map-pokeout para integrar los nuevos criterios de aceptación de spec.md"` |

---

## 5. Estado Actual del Repositorio

- **Rama activa:** `feature/setup-agent-skills`
- **Archivos creados:**
  - [.agents/skills/growme/SKILL.md](file:///c:/Users/antoi/Downloads/All_Files/projects/proyectos-data-engineering/.agents/skills/growme/SKILL.md)
  - [.agents/skills/map-pokeout/SKILL.md](file:///c:/Users/antoi/Downloads/All_Files/projects/proyectos-data-engineering/.agents/skills/map-pokeout/SKILL.md)
  - [essential-agent-skills.md](file:///c:/Users/antoi/Downloads/All_Files/projects/proyectos-data-engineering/essential-agent-skills.md)
