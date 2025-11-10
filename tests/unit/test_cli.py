from pathlib import Path
import json
import numpy as np
import pandas as pd

from qtomography.app import ReconstructionConfig, dump_config_file
from qtomography.cli.main import main as cli_main


def _write_probabilities(tmp_path, data):
    frame = pd.DataFrame(data)
    csv = tmp_path / "probs.csv"
    frame.to_csv(csv, header=False, index=False)
    return csv


def test_cli_reconstruct_creates_summary(tmp_path, capsys):
    data = np.full((16, 1), 1/16, dtype=float)
    input_file = _write_probabilities(tmp_path, data)
    output_dir = tmp_path / "cli"

    exit_code = cli_main(
        [
            "reconstruct",
            str(input_file),
            "--dimension",
            "4",
            "--method",
            "linear",
            "--output-dir",
            str(output_dir),
            "--bell",
        ]
    )
    assert exit_code == 0

    summary = output_dir / "summary.csv"
    assert summary.exists()
    df = pd.read_csv(summary)
    assert "bell_max_fidelity" in df.columns
    assert (df["bell_max_fidelity"] <= 1.0).all()

    # run summarize command against same file
    exit_code = cli_main(["summarize", str(summary), "--metrics", "purity", "trace"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "purity" in captured.out



def test_cli_bell_analyze_command(tmp_path, capsys):
    data = np.full((16, 1), 1/16, dtype=float)
    input_file = _write_probabilities(tmp_path, data)
    output_dir = tmp_path / "cli_bell"

    exit_code = cli_main([
        "reconstruct",
        str(input_file),
        "--dimension",
        "4",
        "--method",
        "linear",
        "--output-dir",
        str(output_dir),
        "--bell",
    ])
    assert exit_code == 0

    records_dir = output_dir / "records"
    output_csv = tmp_path / "bell_summary.csv"
    exit_code = cli_main([
        "bell-analyze",
        str(records_dir),
        "--output",
        str(output_csv),
    ])
    assert exit_code == 0
    assert output_csv.exists()
    df = pd.read_csv(output_csv)
    assert not df.empty


def test_cli_config_file(tmp_path, capsys):
    data = np.full((4, 1), 0.25, dtype=float)
    input_file = _write_probabilities(tmp_path, data)
    output_dir = tmp_path / "cli_config"
    config = ReconstructionConfig(
        input_path=input_file,
        output_dir=output_dir,
        methods=("linear",),
        dimension=2,
        analyze_bell=False,
    )
    config_path = tmp_path / "config.json"
    dump_config_file(config, config_path)
    saved_config_path = tmp_path / "saved.json"

    exit_code = cli_main(["reconstruct", "--config", str(config_path), "--save-config", str(saved_config_path)])
    assert exit_code == 0
    assert saved_config_path.exists()
    summary = output_dir / "summary.csv"
    assert summary.exists()
    df = pd.read_csv(summary)
    assert not df.empty


# ============================================================
# Stage 3.2: CLI summarize 增强功能测试
# ============================================================

def test_cli_summarize_compare_methods(tmp_path, capsys):
    """测试 summarize --compare-methods 功能"""
    # 准备测试数据：3个样本，Linear + MLE
    data = np.array([[0.5, 0.6, 0.4], [0.5, 0.4, 0.6], [0.25, 0.2, 0.15], [0.25, 0.3, 0.25]], dtype=float)
    input_file = _write_probabilities(tmp_path, data)
    output_dir = tmp_path / "compare_test"
    
    # 运行重构生成 summary.csv
    exit_code = cli_main([
        "reconstruct",
        str(input_file),
        "--dimension", "2",
        "--method", "both",
        "--output-dir", str(output_dir)
    ])
    assert exit_code == 0
    
    summary = output_dir / "summary.csv"
    assert summary.exists()
    
    # 测试 --compare-methods
    exit_code = cli_main([
        "summarize",
        str(summary),
        "--compare-methods",
        "--metrics", "purity", "trace"
    ])
    assert exit_code == 0
    
    # 检查输出内容
    captured = capsys.readouterr()
    assert "Linear vs MLE 对比报告" in captured.out
    assert "配对样本:" in captured.out
    assert "指标: purity" in captured.out
    assert "指标: trace" in captured.out
    assert "MLE 优化统计:" in captured.out
    assert "成功率:" in captured.out


def test_cli_summarize_output_csv(tmp_path):
    """测试 summarize --output 保存为 CSV"""
    # 准备测试数据
    data = np.array([[0.5], [0.5], [0.25], [0.25]], dtype=float)
    input_file = _write_probabilities(tmp_path, data)
    output_dir = tmp_path / "output_test"
    
    # 运行重构
    cli_main([
        "reconstruct",
        str(input_file),
        "--dimension", "2",
        "--method", "both",
        "--output-dir", str(output_dir)
    ])
    
    summary = output_dir / "summary.csv"
    report_csv = tmp_path / "report.csv"
    
    # 测试保存 CSV 报告
    exit_code = cli_main([
        "summarize",
        str(summary),
        "--compare-methods",
        "--metrics", "purity", "trace",
        "--output", str(report_csv)
    ])
    assert exit_code == 0
    assert report_csv.exists()
    
    # 验证报告内容
    df = pd.read_csv(report_csv)
    assert not df.empty
    assert "purity" in df.columns or "purity" in str(df.columns)


def test_cli_summarize_output_json(tmp_path):
    """测试 summarize --output 保存为 JSON"""
    # 准备测试数据
    data = np.array([[0.5], [0.5], [0.25], [0.25]], dtype=float)
    input_file = _write_probabilities(tmp_path, data)
    output_dir = tmp_path / "json_test"
    
    # 运行重构
    cli_main([
        "reconstruct",
        str(input_file),
        "--dimension", "2",
        "--method", "both",
        "--output-dir", str(output_dir)
    ])
    
    summary = output_dir / "summary.csv"
    report_json = tmp_path / "report.json"
    
    # 测试保存 JSON 报告
    exit_code = cli_main([
        "summarize",
        str(summary),
        "--compare-methods",
        "--metrics", "purity", "trace",
        "--output", str(report_json)
    ])
    assert exit_code == 0
    assert report_json.exists()
    
    # 验证 JSON 格式
    with report_json.open() as f:
        data = json.load(f)
    assert isinstance(data, dict)
    assert "purity" in data or "linear" in data or "mle" in data


def test_cli_summarize_single_method_warning(tmp_path, capsys):
    """测试仅有单一方法时的警告提示"""
    # 准备只有 linear 的数据
    data = np.array([[0.5], [0.5], [0.25], [0.25]], dtype=float)
    input_file = _write_probabilities(tmp_path, data)
    output_dir = tmp_path / "single_method"
    
    # 仅运行 linear
    cli_main([
        "reconstruct",
        str(input_file),
        "--dimension", "2",
        "--method", "linear",
        "--output-dir", str(output_dir)
    ])
    
    summary = output_dir / "summary.csv"
    
    # 测试 --compare-methods（应该显示警告）
    exit_code = cli_main([
        "summarize",
        str(summary),
        "--compare-methods",
        "--metrics", "purity"
    ])
    assert exit_code == 0
    
    # 检查警告信息
    captured = capsys.readouterr()
    assert "需要同时包含 Linear 和 MLE" in captured.out or "当前方法:" in captured.out


def test_cli_summarize_detailed_mode(tmp_path, capsys):
    """测试 summarize --detailed 功能"""
    # 准备测试数据：3个样本，Linear + MLE
    data = np.array([[0.5, 0.6, 0.4], [0.5, 0.4, 0.6], [0.25, 0.2, 0.15], [0.25, 0.3, 0.25]], dtype=float)
    input_file = _write_probabilities(tmp_path, data)
    output_dir = tmp_path / "detailed_test"
    
    # 运行重构生成 summary.csv
    cli_main([
        "reconstruct",
        str(input_file),
        "--dimension", "2",
        "--method", "both",
        "--output-dir", str(output_dir)
    ])
    
    summary = output_dir / "summary.csv"
    
    # 测试 --compare-methods --detailed
    exit_code = cli_main([
        "summarize",
        str(summary),
        "--compare-methods",
        "--detailed",
        "--metrics", "purity", "trace"
    ])
    assert exit_code == 0
    
    # 检查输出内容（详细模式应该包含 Min, 25%, 75%, Max）
    captured = capsys.readouterr()
    assert "Min" in captured.out
    assert "25%" in captured.out
    assert "75%" in captured.out
    assert "Max" in captured.out
    assert "指标: purity" in captured.out
    assert "指标: trace" in captured.out
