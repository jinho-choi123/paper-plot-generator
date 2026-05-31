from pathlib import Path

import matplotlib.pyplot as plt

from paper_plot.export import export_figure, output_stem


def test_output_stem_removes_known_extension():
    assert output_stem(Path("figures/result.pdf")) == Path("figures/result")
    assert output_stem(Path("figures/result.png")) == Path("figures/result")
    assert output_stem(Path("figures/result")) == Path("figures/result")


def test_output_stem_removes_arbitrary_extension():
    assert output_stem(Path("figures/result.jpeg")) == Path("figures/result")


def test_export_figure_writes_pdf_and_png(tmp_path):
    fig, ax = plt.subplots()
    ax.plot([1, 2], [3, 4])

    written = export_figure(fig, tmp_path / "nested" / "plot.pdf")

    assert written == [
        tmp_path / "nested" / "plot.pdf",
        tmp_path / "nested" / "plot.png",
    ]
    assert written[0].exists()
    assert written[1].exists()
