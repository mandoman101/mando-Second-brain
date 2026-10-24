import json
import os
import sys
from pathlib import Path
import pytest

ADAPTER_DIR = Path('/Users/millie-girl/development/forgepoints-ai-lab/adapter')
if str(ADAPTER_DIR) not in sys.path:
    sys.path.insert(0, str(ADAPTER_DIR))

from forgepoints_adapter import (
    ForgePointsAdapter,
    PathTraversalError,
    SecretLeakError,
    load_config,
)

@pytest.fixture()
def adapter():
    cfg = load_config(str(ADAPTER_DIR / 'config.example.json'))
    return ForgePointsAdapter(cfg)

def test_01_dual_schema_project_notes_written_and_valid(adapter):
    written = adapter.sync_projects_to_vault()
    assert len(written) == 4
    for rel in written:
        val = adapter.vault_ops.validate_note(rel)
        assert val.get('ok') is True, f'Validation failed for {rel}: {val}'
        note = adapter.read_memory(rel)
        content = note['content']
        assert '## For future agent' in content
        assert 'ai-first: true' in content
        assert 'type: project' in content
        assert 'projectDir:' in content
        assert 'category:' in content

def test_02_hypernovum_plugin_installed_in_test_vault(adapter):
    res = adapter.install_hypernovum_plugin_into_vault()
    assert set(res['files']) == {'main.js', 'manifest.json', 'styles.css'}
    cp = json.loads((adapter.vault_path / '.obsidian' / 'community-plugins.json').read_text())
    assert 'hypernovum' in cp

def test_03_propose_and_retrieve_memory_with_source_survival(adapter):
    # Remove any prior test run note first so we test fresh creation + duplicate detection cleanly
    for old in (adapter.vault_path / 'Inbox').glob('*riverpod-34-notifier-migration-fact*'):
        old.unlink()
    res = adapter.propose_memory(
        title='Riverpod 3.4 Notifier Migration Fact',
        content='Riverpod 3.4.3 uses Notifier and AsyncNotifier as the primary reactive primitives.',
        note_type='research',
        tags=['research', 'flutter', 'riverpod'],
        source_ref='https://pub.dev/packages/riverpod',
        project_link='kaysNails Flutter App',
        confidence='stated',
        verification_status='verified',
        agent_id='analyst'
    )
    assert res.get('duplicate') is False
    assert res.get('path', '').startswith('Inbox/')
    # Retrieve via second agent session (fresh adapter instance)
    adapter2 = ForgePointsAdapter(load_config(str(ADAPTER_DIR / 'config.example.json')))
    hits = adapter2.search_memory('Riverpod 3.4.3 Notifier')
    assert any('riverpod-34-notifier-migration-fact' in h['path'] for h in hits)
    read_back = adapter2.read_memory(res['path'])
    assert 'https://pub.dev/packages/riverpod' in read_back['content']
    assert '[[Projects/kaysNails Flutter App]]' in read_back['content']

def test_04_duplicate_ingestion_is_idempotent(adapter):
    res1 = adapter.propose_memory(
        title='Riverpod 3.4 Notifier Migration Fact',
        content='Riverpod 3.4.3 uses Notifier and AsyncNotifier as the primary reactive primitives.',
        source_ref='https://pub.dev/packages/riverpod',
        agent_id='analyst'
    )
    assert res1['duplicate'] is True
    assert res1['saved'] is False

def test_05_unauthorized_agent_write_rejected(adapter):
    with pytest.raises(PermissionError):
        adapter.propose_memory(
            title='Unauthorized Note',
            content='Should not be written.',
            agent_id='unauthorized'
        )

def test_06_secret_exclusion_rejects_credentials(adapter):
    fake_secret = 'api_key = "' + 'sk-' + ('A1b2C3d4E5f6' * 3) + '"'
    with pytest.raises(SecretLeakError):
        adapter.propose_memory(
            title='Config Dump',
            content=f'Here is a key {fake_secret}',
            agent_id='coder'
        )

def test_07_path_traversal_and_protected_dirs_blocked(adapter):
    with pytest.raises(PathTraversalError):
        adapter.read_memory('../../etc/passwd')
    with pytest.raises(PathTraversalError):
        adapter._guard_vault_path('raw/immutable.md')

def test_08_live_cluster_heartbeats_and_offline_representation(adapter):
    live_snaps = adapter.sync_cluster_heartbeats()
    assert len(live_snaps) == 4
    sim_telemetry = {
        'nodes': [
            {'id': 'm3-max-mbp', 'online': True, 'gpuPct': 45, 'avgCpu': 22.0, 'ramUsed': 53.6, 'ramTotal': 64.0, 'modelLabel': 'Qwen3.6-35B-8bit'},
            {'id': 'ty-bot', 'online': False},
            {'id': 'mando-bot', 'online': True, 'gpuPct': 0, 'avgCpu': 4.0, 'ramUsed': 19.2, 'ramTotal': 24.0, 'modelLabel': 'Qwen3-Coder-30B'},
            {'id': 'millie-girl', 'online': True, 'gpuPct': 5, 'avgCpu': 8.0, 'ramUsed': 9.1, 'ramTotal': 16.0, 'modelLabel': 'Gateway'},
        ]
    }
    snaps = adapter.sync_cluster_heartbeats(telemetry_override=sim_telemetry)
    by_id = {s['sessionId']: s for s in snaps}
    assert by_id['agent-architect-m3max']['state'] == 'running'
    assert 'stoppedAt' not in by_id['agent-architect-m3max']
    assert by_id['agent-analyst-tybot']['state'] == 'complete'
    assert isinstance(by_id['agent-analyst-tybot'].get('stoppedAt'), int)
    adapter.sync_cluster_heartbeats()
