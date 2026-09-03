"""
Módulo de integración con Socrata Open Data API (SODA) para Datos Abiertos Colombia (datos.gov.co).
Implementa Spec-Driven Development conforme a spec.md y decisions.md (ADR-001, ADR-003, ADR-004).
"""
from .soda_client import SocrataClient

__all__ = ["SocrataClient"]
