# Battery CI rendering

Pull request CI runs the PyBaMM solver checks, result and provenance validation, and the short Manim smoke render. The 24-second Blender plus Manim mixed preview is available only through `workflow_dispatch` and does not run for pull requests or pushes.

GitHub Actions permits manual dispatch only when the workflow file exists on the repository's default branch. Until this workflow change reaches the default branch, use the documented local rendering pipeline for a full preview.

The local command remains:

```bash
uv run python scripts/produce_lesson.py \
  --spec examples/education/battery_spm_smoke.json \
  --solver-result <validated-solver-result-path> \
  --preview
```

The supplied solver result must pass the existing battery result validation contract.
