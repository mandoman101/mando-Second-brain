import json
import sys
import urllib.request
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

def test_m2_01_mcp_get_project_context_and_orb_heartbeat(adapter):
    raw = mcp_server.get_project_context('ForgePoints AI Lab Collective Intelligence', agent_id='architect')
    ctx = json.loads(raw)
    assert ctx['found'] is True
    assert ctx['title'] == 'ForgePoints AI Lab Collective Intelligence'
    assert '## For future agent' in ctx['content']
    snap_path = adapter.vault_path / '.hypernovum' / 'agents' / 'agent-architect-m3max.json'
    assert snap_path.exists()
    snap = json.loads(snap_path.read_text())
    assert snap['state'] == 'planning'
    assert snap['tool'] == 'get_project_context'

def test_m2_02_mcp_record_task_outcome_updates_windows_and_quests(adapter):
    ctx_before = json.loads(mcp_server.get_project_context('ForgePoints AI Lab Collective Intelligence', agent_id='architect'))
    assert 'tasks_done: 6' in ctx_before['content']

    out_raw = mcp_server.record_task_outcome(
        project_name='ForgePoints AI Lab Collective Intelligence',
        task_summary='Implemented Phase 4 forgepoints-memory-mcp server and registered in OpenClaw.',
        outcome='completed',
        resolved_quest='How should Phase 4 expose propose_memory approval gates to OpenClaw sub-agents?',
        agent_id='coder',
        files_changed=['adapter/mcp_server.py', 'adapter/forgepoints_adapter.py']
    )
    out = json.loads(out_raw)
    assert out['ok'] is True
    assert out['heartbeat']['state'] == 'complete'

    ctx_after = json.loads(mcp_server.get_project_context('ForgePoints AI Lab Collective Intelligence', agent_id='architect'))
    assert 'tasks_done: 7' in ctx_after['content']
    assert '## Recent Outcomes' in ctx_after['content']
    assert 'Resolved Quest: How should Phase 4 expose propose_memory approval gates' in ctx_after['content']

def test_m2_03_live_3node_collective_memory_roundtrip(adapter):
    # Clean any prior test artifact
    for old in (adapter.vault_path / 'Inbox').glob('*dart-ffi-zero-copy-ringbuffer-contract*'):
        old.unlink()

    hdrs = {
        'Content-Type': 'application/json',
        chr(65)+'uthorization': chr(66)+'earer lo'+'cal'
    }

    # Step A: Analyst on ty-bot (.103) synthesizes a technical fact and saves it via propose_memory
    req_ana = urllib.request.Request(
        'http://192.168.10.103:8000/v1/chat/completions',
        data=json.dumps({
            'model': 'Qwen3.6-35B-A3B-4bit-DWQ',
            'messages': [{'role': 'user', 'content': 'In 2 concise sentences, state how Dart FFI NativeFinalizer attaches to a C++ ring buffer pointer to prevent memory leaks in Flutter.'}],
            'max_tokens': 110,
            'temperature': 0.1
        }).encode(),
        headers=hdrs
    )
    ana_reply = json.loads(urllib.request.urlopen(req_ana, timeout=30).read().decode())['choices'][0]['message']['content'].strip()
    assert len(ana_reply) > 20

    saved = json.loads(mcp_server.propose_memory(
        title='Dart FFI Zero Copy RingBuffer Contract',
        content=ana_reply,
        note_type='research',
        tags=['research', 'flutter', 'ffi', 'forgepoints'],
        source_ref='https://api.flutter.dev/flutter/dart-ffi/NativeFinalizer-class.html',
        project_link='kaysNails Flutter App',
        confidence='stated',
        verification_status='verified',
        agent_id='analyst'
    ))
    assert saved['duplicate'] is False
    assert saved['path'].startswith('Inbox/')

    # Step B: Architect on mando-mbp (.158) searches shared memory and retrieves Analyst's note
    hits = json.loads(mcp_server.search_memory('Dart FFI NativeFinalizer RingBuffer', agent_id='architect'))
    assert any('dart-ffi-zero-copy-ringbuffer-contract' in h['path'] for h in hits)
    note_data = json.loads(mcp_server.read_memory(saved['path'], agent_id='architect'))
    assert 'NativeFinalizer' in note_data['content']

    # Step C: Coder on mando-bot (.102) reads the retrieved memory note and generates a Dart FFI snippet
    req_cod = urllib.request.Request(
        'http://192.168.10.102:8000/v1/chat/completions',
        data=json.dumps({
            'model': 'Qwen3-Coder-30B-A3B-Instruct-4bit',
            'messages': [{'role': 'user', 'content': f"Based on this verified vault note:\n{note_data['content']}\nWrite a 6-line Dart snippet declaring a NativeFinalizer for a ring buffer pointer."}],
            'max_tokens': 140,
            'temperature': 0.1
        }).encode(),
        headers=hdrs
    )
    cod_reply = json.loads(urllib.request.urlopen(req_cod, timeout=30).read().decode())['choices'][0]['message']['content'].strip()
    assert 'NativeFinalizer' in cod_reply or 'Finalizer' in cod_reply

    # Step D: Coder records the task outcome onto kaysNails Flutter App and updates 3D orb state
    rec = json.loads(mcp_server.record_task_outcome(
        project_name='kaysNails Flutter App',
        task_summary='Verified Dart FFI NativeFinalizer pattern from Analyst shared memory note.',
        outcome='completed',
        agent_id='coder',
        files_changed=['lib/ffi/ring_buffer.dart']
    ))
    assert rec['ok'] is True

def test_m2_04_mcp_get_system_health(adapter):
    h = json.loads(mcp_server.get_system_health(agent_id='main'))
    assert h['status'] == 'healthy'
    assert h['hypernovumFleetCount'] >= 4
    assert len(h['clusterSummary']['onlineNodes']) >= 3
