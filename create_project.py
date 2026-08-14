"""
Script de automatización para generar la estructura inicial (scaffolding) 
de nuevos proyectos de Ingeniería de Datos.

Uso:
    python create_project.py <nombre_del_proyecto>

Ejemplo:
    python create_project.py otro_cliente
"""

import sys
from pathlib import Path

SUBDIRECTORIES = [
    "config",
    "notebooks",
    "pipelines",
    ".github/workflows",
]

def scaffold_project(name: str):
    root_dir = Path(__file__).parent.resolve()
    
    clean_name = name.strip().lower().replace("-", "_").replace(" ", "_")
    folder_name = clean_name if clean_name.endswith("_project") else f"{clean_name}_project"
    
    project_path = root_dir / folder_name
    
    if project_path.exists():
        print(f"⚠️ El directorio '{folder_name}' ya existe en {project_path}")
        return

    print(f"🚀 Generando scaffolding para el proyecto: '{folder_name}'...\n")
    project_path.mkdir(parents=True, exist_ok=True)

    for sub in SUBDIRECTORIES:
        sub_path = project_path / sub
        sub_path.mkdir(parents=True, exist_ok=True)
        (sub_path / ".gitkeep").write_text("# gitkeep\n", encoding="utf-8")
        print(f"  ├── 📂 {sub}/")

    readme = project_path / "README.md"
    readme_content = f"# {folder_name}\n\nEstructura base de proyecto de Ingeniería de Datos.\n"
    readme.write_text(readme_content, encoding="utf-8")
    print(f"  └── 📄 README.md\n")

    print(f"✅ Proyecto '{folder_name}' creado exitosamente en {project_path}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        project_name = sys.argv[1]
    else:
        project_name = input("Nombre del proyecto: ").strip()

    if project_name:
        scaffold_project(project_name)
    else:
        print("❌ Error: Debes ingresar un nombre válido.")
