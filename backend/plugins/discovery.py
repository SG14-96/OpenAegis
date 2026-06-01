from pathlib import Path

from schema.PluginManifest import PluginManifest


def discover_plugins() -> list[dict]:
    """
    Walk plugins/<manufacturer>/<model>/ and return one entry per manufacturer
    with a nested list of its models.

    Example:
        [{"manufacturer": "DSC", "models": [{"name": "IT-100_Integration_Module",
                                              "module_path": "plugins.DSC.IT-100_Integration_Module",
                                              "manifest": {...}}]}]
    """
    plugins_dir = Path(__file__).parent
    result = []
    for manufacturer in sorted(plugins_dir.iterdir()):
        if not manufacturer.is_dir() or not (manufacturer / "__init__.py").exists():
            continue
        models = []
        for model in sorted(manufacturer.iterdir()):
            if not model.is_dir() or not (model / "__init__.py").exists():
                continue
            manifest_path = model / "manifest.json"
            manifest = PluginManifest.from_file(manifest_path).model_dump() if manifest_path.exists() else None
            models.append({
                "name": model.name,
                "module_path": f"plugins.{manufacturer.name}.{model.name}",
                "manifest": manifest,
            })
        if models:
            result.append({"manufacturer": manufacturer.name, "models": models})
    return result
