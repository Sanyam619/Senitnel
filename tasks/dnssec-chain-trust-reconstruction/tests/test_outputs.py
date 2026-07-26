import json
import shutil
import subprocess
from pathlib import Path

APP = Path('/app')
OUT = APP / 'output'


def run_tool():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    subprocess.run(
        ['cargo', 'run', '--quiet', '--manifest-path', '/app/Cargo.toml', '--', '/app/data/queries.tsv', '/app/output'],
        check=True,
        cwd=APP,
        timeout=120,
    )
    return json.loads((OUT / 'validation.json').read_text()), json.loads((OUT / 'replayed.json').read_text())


def idx(rows):
    return {row['id']: row for row in rows}


def root(zone, child):
    return f'root:{zone}->{child}'


def link(left, right):
    return f'{left}->{right}'


def assert_row(row, status, chain, reason):
    assert row['status'] == status
    assert row['chain'] == chain
    assert row['reason'] == reason


def manifest_rows():
    rows = {}
    for line in (APP / 'data' / 'queries.tsv').read_text().splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        kind, qid, name, instant = line.split('|')
        if kind == 'Q':
            rows[qid] = (name, int(instant))
    return rows


def test_alpha():
    """The primary overlap prefers the later usable route while earlier quiet traffic remains accepted."""
    got = idx(run_tool()[0])
    assert_row(got['q01'], 'valid', [root('example.test', 'KSK_A'), link('KSK_A', 'ZSK_OLD'), link('ZSK_OLD', 'www.example.test')], 'sig-e-old')
    assert_row(got['q02'], 'valid', [root('example.test', 'KSK_B'), link('KSK_B', 'ZSK_NEW'), link('ZSK_NEW', 'www.example.test')], 'sig-e-new')
    assert_row(got['q04'], 'valid', [root('example.test', 'KSK_B'), link('KSK_B', 'ZSK_NEW'), link('ZSK_NEW', 'api.example.test')], 'sig-e-api')


def test_bravo():
    """A stale-only primary route is rejected and marked with the replay reason."""
    got = idx(run_tool()[0])
    assert_row(got['q03'], 'invalid', [], 'replayed')


def test_charlie():
    """The secondary fixture changes routes after its handoff instant."""
    got = idx(run_tool()[0])
    assert_row(got['q05'], 'valid', [root('lab.example.test', 'LKSK_A'), link('LKSK_A', 'LZSK_A'), link('LZSK_A', 'lab.example.test')], 'sig-l-old')
    assert_row(got['q06'], 'valid', [root('lab.example.test', 'LKSK_B'), link('LKSK_B', 'LZSK_B'), link('LZSK_B', 'lab.example.test')], 'sig-l-new')


def test_delta():
    """The archive boundary changes route exactly at the handoff instant."""
    got = idx(run_tool()[0])
    assert_row(got['q07'], 'valid', [root('archive.example.test', 'AKSK_A'), link('AKSK_A', 'AZSK_A'), link('AZSK_A', 'cold.archive.example.test')], 'sig-a-old')
    assert_row(got['q08'], 'valid', [root('archive.example.test', 'AKSK_B'), link('AKSK_B', 'AZSK_B'), link('AZSK_B', 'cold.archive.example.test')], 'sig-a-new')


def test_echo():
    """The replay report contains exactly the stale-only query ids."""
    rows, replayed = run_tool()
    got = idx(rows)
    assert_row(got['q09'], 'invalid', [], 'replayed')
    assert replayed == {'queries': ['q03', 'q09']}


def test_foxtrot():
    """Missing material remains invalid without being reported as replayed."""
    rows, replayed = run_tool()
    got = idx(rows)
    assert_row(got['q10'], 'invalid', [], 'no_path')
    assert set(got) == set(manifest_rows())
    assert replayed == {'queries': ['q03', 'q09']}


def test_golf():
    """Each validation row echoes the query identity, lookup name, and capture instant."""
    expected = manifest_rows()
    rows, _ = run_tool()
    got = idx(rows)
    assert set(got) == set(expected)
    for qid, (name, instant) in expected.items():
        row = got[qid]
        assert row['id'] == qid
        assert row['name'] == name
        assert row['instant'] == instant


def test_hotel():
    """Repeated runs over the same manifest emit identical validation and replay artifacts."""
    rows_a, replay_a = run_tool()
    rows_b, replay_b = run_tool()
    assert rows_a == rows_b
    assert replay_a == replay_b
