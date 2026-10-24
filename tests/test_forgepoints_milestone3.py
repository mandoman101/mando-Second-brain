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

def test_m3_01_single_writer_lock_acquisition_and_denial(adapter):
    # Coder claims lib/main.dart on kaysNails Flutter App
    claim1 = json.loads(mcp_server.claim_file_scope(
        agent_id='coder',
        project_name='kaysNails Flutter App',
        file_path='lib/main.dart',
        action='Refactoring app router'
    ))
    assert claim1['acquired'] is True
    assert claim1['conflict'] is False
    assert claim1['file'] == 'lib/main.dart'

    # Architect attempts to claim the exact same file while Coder is editing -> denied!
    claim2 = json.loads(mcp_server.claim_file_scope(
        agent_id='architect',
        project_name='kaysNails Flutter App',
        file_path='./lib/main.dart',
        action='Concurrent edit attempt'
    ))
    assert claim2['acquired'] is False
    assert claim2['conflict'] is True
    assert claim2['holderSessionId'] == 'agent-coder-mandobot'

def test_m3_02_deterministic_same_file_conflict_detection(adapter):
    # Force two sessions onto the same file via direct emit_agent_activity to verify ConflictDetector
    adapter.emit_agent_activity(
        agent_id='coder',
        state='editing',
        action='Editing router.dart',
        project_title='kaysNails Flutter App',
        tool_name='write_remote_file',
        file_path='lib/router.dart'
    )
    adapter.emit_agent_activity(
        agent_id='architect',
        state='editing',
        action='Reviewing/editing router.dart',
        project_title='kaysNails Flutter App',
        tool_name='write_remote_file',
        file_path='lib/router.dart'
    )
    conflicts = json.loads(mcp_server.detect_active_conflicts())
    same_file = [c for c in conflicts if c['kind'] == 'same-file' and 'lib/router.dart' in c['files']]
    assert len(same_file) == 1
    assert same_file[0]['severity'] == 'high'
    assert set(same_file[0]['sessions']) == {'agent-architect-m3max', 'agent-coder-mandobot'}

def test_m3_03_conflict_clears_when_task_completed(adapter):
    # Complete Coder's task on kaysNails Flutter App so it transitions out of 'editing'
    mcp_server.record_task_outcome(
        project_name='kaysNails Flutter App',
        task_summary='Finished router.dart refactoring.',
        outcome='completed',
        agent_id='coder',
        files_changed=['lib/router.dart']
    )
    # Move Architect back to planning on ForgePoints AI Lab Collective Intelligence
    mcp_server.get_project_context('ForgePoints AI Lab Collective Intelligence', agent_id='architect')
    conflicts = json.loads(mcp_server.detect_active_conflicts())
    same_file = [c for c in conflicts if c['kind'] == 'same-file' and 'lib/router.dart' in c.get('files', [])]
    assert len(same_file) == 0

def test_m3_04_system_health_includes_conflict_telemetry(adapter):
    adapter.sync_cluster_heartbeats()
    health = json.loads(mcp_server.get_system_health(agent_id='main'))
    assert 'activeConflicts' in health
    assert isinstance(health['activeConflicts'], list)
    assert health['status'] == 'healthy'
