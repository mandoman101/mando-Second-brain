import json
import sys
from pathlib import Path
import pytest

ADAPTER_DIR = Path('/Users/millie-girl/development/forgepoints-ai-lab/adapter')
if str(ADAPTER_DIR) not in sys.path:
    sys.path.insert(0, str(ADAPTER_DIR))

from forgepoints_adapter import ForgePointsAdapter, load_config
import mcp_server

@pytest.fixture()
def adapter():
    cfg = load_config(str(ADAPTER_DIR / 'config.example.json'))
    adp = ForgePointsAdapter(cfg)
    adp.sync_projects_to_vault()
    return adp

def test_m4_01_graduate_memory_promotes_note_and_leaves_redirect_stub(adapter):
    # Clean any prior test artifacts
    for f in (adapter.vault_path / 'Inbox').glob('*omlx-turboquant-6bit-kv-benchmark*'):
        f.unlink()
    for f in (adapter.vault_path / 'Knowledge').glob('*omlx-turboquant-6bit-kv-benchmark*'):
        f.unlink()

    prop = json.loads(mcp_server.propose_memory(
        title='oMLX TurboQuant 6bit KV Benchmark',
        content='On ty-bot 32GB M4, 6-bit TurboQuant KV supports 131,072 context tokens at 33.3 tok/s with zero swap.',
        note_type='research',
        tags=['research', 'omlx', 'kv-cache'],
        source_ref='http://192.168.10.103:8000/v1/models',
        project_link='ForgePoints AI Lab Collective Intelligence',
        confidence='stated',
        verification_status='verified',
        agent_id='analyst'
    ))
    inbox_rel = prop['path']
    grad = json.loads(mcp_server.graduate_memory(inbox_rel_path=inbox_rel, target_folder='Knowledge', reviewer_agent_id='architect'))
    assert grad['ok'] is True
    assert grad['to'].startswith('Knowledge/')

    # Verify canonical note exists in Knowledge/ with verification_status: verified
    canon = json.loads(mcp_server.read_memory(grad['to'], agent_id='architect'))['content']
    assert 'verification_status: verified' in canon
    assert '131,072 context tokens' in canon

    # Verify non-destructive redirect stub remains in Inbox/
    stub = json.loads(mcp_server.read_memory(inbox_rel, agent_id='architect'))['content']
    assert 'type: redirect' in stub
    assert 'Graduated to [[' in stub

def test_m4_02_supersede_memory_preserves_history_and_demotes_old_note(adapter):
    for f in (adapter.vault_path / 'Knowledge').glob('*state-management-adr*'):
        f.unlink()
    for f in (adapter.vault_path / 'Inbox').glob('*state-management-adr*'):
        f.unlink()

    p_old = json.loads(mcp_server.propose_memory(
        title='State Management ADR v1 Legacy Provider',
        content='kaysNails uses legacy ChangeNotifierProvider for cart state management.',
        note_type='decision',
        agent_id='architect'
    ))
    g_old = json.loads(mcp_server.graduate_memory(p_old['path'], target_folder='Knowledge', reviewer_agent_id='architect'))

    p_new = json.loads(mcp_server.propose_memory(
        title='State Management ADR v2 Riverpod Notifier',
        content='kaysNails migrated to Riverpod 3.4.3 Notifier and AsyncNotifier for cart state management.',
        note_type='decision',
        source_ref='https://pub.dev/packages/riverpod',
        agent_id='architect'
    ))
    g_new = json.loads(mcp_server.graduate_memory(p_new['path'], target_folder='Knowledge', reviewer_agent_id='architect'))

    sup = json.loads(mcp_server.supersede_memory(
        old_rel_path=g_old['to'],
        new_rel_path=g_new['to'],
        reason='Upgraded to Riverpod 3.4.3 Notifier architecture',
        agent_id='architect'
    ))
    assert sup['ok'] is True

    # Verify old note is NOT deleted, has status: superseded, and links to replacement
    old_txt = json.loads(mcp_server.read_memory(g_old['to'], agent_id='analyst'))['content']
    assert 'status: superseded' in old_txt
    assert 'superseded_by:' in old_txt

def test_m4_03_sqlite_fts5_hybrid_index_ranks_active_verified_above_superseded(adapter):
    idx = json.loads(mcp_server.rebuild_search_index(agent_id='analyst'))
    assert idx['ok'] is True
    assert idx['notesIndexed'] >= 6
    assert Path(idx['dbPath']).exists()

    hits = json.loads(mcp_server.hybrid_search_memory('kaysNails cart state management Riverpod', limit=6, agent_id='analyst'))
    assert len(hits) >= 2
    paths = [h['path'] for h in hits]
    v2_idx = next(i for i, p in enumerate(paths) if 'state-management-adr-v2' in p)
    v1_idx = next(i for i, p in enumerate(paths) if 'state-management-adr-v1' in p)
    # Active verified v2 ADR must outrank superseded v1 ADR!
    assert v2_idx < v1_idx
    assert hits[v1_idx]['status'] == 'superseded'

def test_m4_04_audit_memory_freshness_reports_verified_and_superseded_counts(adapter):
    audit = json.loads(mcp_server.audit_memory_freshness(stale_days=30))
    assert audit['totalScanned'] >= 6
    assert audit['verifiedCount'] >= 4
    assert audit['supersededCount'] >= 1
