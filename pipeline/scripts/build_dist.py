from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def build_dist() -> Path:
    """Build the Astro static site and assemble the dist/ directory."""
    # Astro project lives at the repo root (parent of pipeline/)
    pipeline_dir = Path(__file__).resolve().parents[1]
    repo_root = pipeline_dir.parent
    dist_dir = repo_root / "dist"

    # Ensure npm dependencies are installed
    node_modules = repo_root / "node_modules"
    if not node_modules.exists():
        print("Instalando dependencias npm...")
        subprocess.run(["npm", "install"], cwd=str(repo_root), check=True)

    # Run Astro build
    print("Ejecutando astro build...")
    subprocess.run(["npm", "run", "build"], cwd=str(repo_root), check=True)

    # Astro outputs to <repo_root>/dist/ by default
    if not dist_dir.exists():
        raise FileNotFoundError(f"No se encontró output de Astro en {dist_dir}.")

    print(f"Build estático listo en: {dist_dir}")
    return dist_dir


def main() -> None:
    build_dist()


if __name__ == "__main__":
    main()
