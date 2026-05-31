from pathlib import Path

from paper_plot.cli import main


def test_cli_generates_pdf_and_png_for_line_series(tmp_path):
    csv_path = tmp_path / "line.csv"
    csv_path.write_text(
        "System,X,Latency\nGPU,1,0.1\nGPU,2,0.2\nPimba,1,0.08\nPimba,2,0.12\n",
        encoding="utf-8",
    )
    output_path = tmp_path / "figures" / "line"
    config_path = tmp_path / "line.yaml"
    config_path.write_text(
        f"""
plot:
  type: line_series
data:
  path: {csv_path}
  columns:
    series: System
    x: X
    y: Latency
output:
  path: {output_path}
order:
  series: [GPU, Pimba]
""",
        encoding="utf-8",
    )

    exit_code = main([str(config_path)])

    assert exit_code == 0
    assert output_path.with_suffix(".pdf").exists()
    assert output_path.with_suffix(".png").exists()
