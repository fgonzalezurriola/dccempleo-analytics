from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def _copy_processed_datasets_to_assets(processed_dir: Path, assets_dir: Path) -> list[Path]:
    assets_dataset_dir = assets_dir / "datasets"
    assets_dataset_dir.mkdir(parents=True, exist_ok=True)

    copied: list[Path] = []
    for json_path in sorted(processed_dir.glob("*.json")):
        destination = assets_dataset_dir / json_path.name
        shutil.copy2(json_path, destination)
        copied.append(destination)
    return copied


def _resolve_frontend_output_dir() -> Path:
    candidates = [Path(".web/build/client"), Path(".web/_static")]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        "No se encontro output de Reflex en .web/build/client ni en .web/_static."
    )


def build_dist() -> Path:
    processed_dir = Path("data/processed")
    assets_dir = Path("assets")
    dist_dir = Path("dist")

    if not processed_dir.exists():
        raise FileNotFoundError(f"No existe {processed_dir}. Corre analisis antes de exportar.")

    copied_assets = _copy_processed_datasets_to_assets(
        processed_dir=processed_dir, assets_dir=assets_dir
    )
    print(f"Datasets copiados a assets: {len(copied_assets)}")

    subprocess.run(["uv", "run", "reflex", "export", "--frontend-only", "--no-zip"], check=True)

    frontend_output = _resolve_frontend_output_dir()
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    dist_dir.mkdir(parents=True, exist_ok=True)

    shutil.copytree(frontend_output, dist_dir, dirs_exist_ok=True)

    dist_assets_dir = dist_dir / "assets"
    if assets_dir.exists():
        shutil.copytree(assets_dir, dist_assets_dir, dirs_exist_ok=True)

    dist_dataset_dir = dist_dir / "datasets"
    dist_dataset_dir.mkdir(parents=True, exist_ok=True)
    for json_path in sorted(processed_dir.glob("*.json")):
        shutil.copy2(json_path, dist_dataset_dir / json_path.name)

    print(f"Build estatico listo en: {dist_dir}")
    return dist_dir


def main() -> None:
    build_dist()


if __name__ == "__main__":
    main()
