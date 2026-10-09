# Robot asset catalog

`scripts/manage_assets.py list` and `search` inspect the local registry; search is not external web search. `fetch` verifies an asset already present in this repository and does not download unpinned files. Conversion requires an explicitly injected converter.

The validated example is `blender.open_manipulator_x.v1`, already vendored under `assets/open_manipulator_x`. It was not downloaded again. Source revision: `0a4af6a923b8b7d80b8c20506d1839c54d2e993e`; aggregate local SHA-256: `68f4a7a8336a5a1696280f24b8309efbd50b5358a294263153853446498c596e`. See [validation report](ASSET_VALIDATION_REPORT.md) and [license notes](ASSET_LICENSES.md).
