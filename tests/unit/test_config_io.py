import json
from pathlib import Path

import pytest

from qtomography.app import (
    ReconstructionConfig,
    config_to_payload,
    dump_config_file,
    load_config_file,
)


def _make_config(tmp_path: Path) -> ReconstructionConfig:
    input_path = tmp_path / 'probabilities.csv'
    input_path.write_text('0.5,0.5,0.25,0.25\n', encoding='utf-8')
    output_dir = tmp_path / 'results'
    return ReconstructionConfig(
        input_path=input_path,
        output_dir=output_dir,
        methods=('linear',),
        dimension=2,
        sheet=0,
        column_range=(1, 1),
        linear_regularization=1e-5,
        wls_regularization=None,
        wls_max_iterations=1500,
        tolerance=1e-8,
        cache_projectors=False,
        analyze_bell=True,
    )


def test_config_to_payload_serialises_paths(tmp_path: Path) -> None:
    config = _make_config(tmp_path)
    payload = config_to_payload(config)
    assert payload['input_path'] == str(config.input_path)
    assert payload['output_dir'] == str(config.output_dir)
    assert payload['methods'] == ['linear']
    assert payload['dimension'] == 2
    assert payload['sheet'] == 0
    assert payload['column_range'] == [1, 1]
    assert payload['linear_regularization'] == pytest.approx(1e-5)
    assert payload['tolerance'] == pytest.approx(1e-8)
    assert payload['cache_projectors'] is False
    assert payload['analyze_bell'] is True


def test_round_trip_config_file(tmp_path: Path) -> None:
    config = _make_config(tmp_path)
    config_path = tmp_path / 'config.json'
    dump_config_file(config, config_path)

    loaded = load_config_file(config_path)
    assert loaded.input_path == config.input_path
    assert loaded.output_dir == config.output_dir
    assert loaded.methods == config.methods
    assert loaded.dimension == config.dimension
    assert loaded.sheet == config.sheet
    assert loaded.column_range == config.column_range
    assert loaded.linear_regularization == config.linear_regularization
    assert loaded.wls_max_iterations == config.wls_max_iterations
    assert loaded.tolerance == config.tolerance
    assert loaded.cache_projectors is False
    assert loaded.analyze_bell is True


def test_load_config_resolves_relative_paths(tmp_path: Path) -> None:
    config_dir = tmp_path / 'configs'
    config_dir.mkdir()
    (tmp_path / 'prob.csv').write_text('0.5,0.5,0.25,0.25\n', encoding='utf-8')

    payload = {
        'input_path': '../prob.csv',
        'output_dir': '../out',
        'methods': ['linear', 'wls'],
    }

    path = config_dir / 'config.json'
    path.write_text(json.dumps(payload), encoding='utf-8')

    loaded = load_config_file(path)
    assert loaded.input_path == tmp_path / 'prob.csv'
    assert loaded.output_dir == tmp_path / 'out'
    assert loaded.methods == ('linear', 'wls')


@pytest.mark.parametrize(
    'field, value, message',
    [
        ('input_path', None, "Missing required field 'input_path'"),
        ('output_dir', None, "Missing required field 'output_dir'"),
        ('dimension', 'two', 'dimension must be an integer'),
        ('tolerance', -1, 'tolerance must be positive'),
        ('wls_max_iterations', 0, 'wls_max_iterations must be a positive integer'),
    ],
)
def test_invalid_configuration_raises(tmp_path: Path, field: str, value, message: str) -> None:
    payload = {
        'input_path': 'prob.csv',
        'output_dir': 'out',
    }
    payload[field] = value
    path = tmp_path / 'bad.json'
    path.write_text(json.dumps(payload), encoding='utf-8')

    with pytest.raises(ValueError) as exc:
        load_config_file(path)
    assert message in str(exc.value)
