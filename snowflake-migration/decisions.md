# Bitácora de Decisiones de Arquitectura (Decisions Log)

## [ADR-001] Adopción de Interfaz Tipo Aplicación (App Layout) y Menú Lateral Fijo
- **Fecha:** 2026-09-25
- **Estado:** Aprobado
- **Contexto:** Los reportes analíticos para comités directivos requieren una experiencia inmersiva similar a un producto SaaS moderno, en lugar de la experiencia genérica de Power BI con pestañas inferiores.
- **Decisión Tomada:** Se establece una barra lateral fija izquierda ($220\text{ px}$) en color grafito oscuro (`#111827`) que contendrá el componente interactivo nativo `Page Navigator`. Las pestañas inferiores del reporte se configuran en modo oculto (`HiddenInViewMode`), de modo que al publicarse en Fabric Service o visualizarse en pantalla completa, la navegación sea exclusivamente a través de la barra lateral.
- **Alternativas Consideradas:**
  - *Pestañas nativas inferiores:* Descartadas por brindar una experiencia poco profesional y ocupar espacio vertical valioso.
  - *Botones individuales manuales con marcadores:* Descartados por alto costo de mantenimiento al añadir o reorganizar páginas.
- **Consecuencias:** Mayor usabilidad, diseño uniforme entre páginas y mantenimiento simplificado gracias a `Page Navigator`.

---

## [ADR-002] Panel Flotante de Filtros (Flyout Slicer Panel) Desacoplado de Datos
- **Fecha:** 2026-09-25
- **Estado:** Aprobado
- **Contexto:** Colocar múltiples segmentadores directamente sobre el lienzo reduce drásticamente el espacio disponible para los visuales principales (gráficos de áreas, dispersión, árbol de descomposición).
- **Decisión Tomada:** Se implementa un panel lateral colapsable (Flyout Drawer) agrupado en `Panel_Filtros`, controlado por dos marcadores: `Filtros_Open` y `Filtros_Closed`.
- **Ajuste Técnico Crítico:** Ambos marcadores deben tener obligatoriamente **`Data: OFF`** (desmarcado).
- **Consecuencias:**
  - Si `Data` estuviese activo, al abrir o cerrar el panel se sobreescribirían o reiniciarían los filtros aplicados por el usuario.
  - Con `Data: OFF`, el marcador únicamente altera la visibilidad del contenedor visual (`Display: ON`) en la página actual (`Current Page: ON`), preservando al 100% el contexto de filtrado interactivo.

---

## [ADR-003] Sincronización Bidireccional entre Fabric MCP y Formato PBIR
- **Fecha:** 2026-09-25
- **Estado:** Aprobado
- **Contexto:** El proyecto utiliza Microsoft Fabric (`ws_dp600-prep`) sincronizado con Git y Power BI Project (PBIR). Se requiere validar los recursos analíticos en Fabric a través de `@microsoft/fabric-mcp` y la API de Fabric.
- **Decisión Tomada:** El agente consulta y mapea mediante Fabric MCP y Azure CLI los IDs de workspace, carpetas, modelos semánticos y reportes, asegurando que el modelo `sm_tpch_gold_directlake` y el reporte `rp_tpch_gold_directlake` mantengan consistencia total de linaje en Direct Lake.
- **Consecuencias:** Linaje trazable de extremo a extremo (Lakehouse Gold $\rightarrow$ Semantic Model Direct Lake $\rightarrow$ PBIR Report $\rightarrow$ Fabric Service).
