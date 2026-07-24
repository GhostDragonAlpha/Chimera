#!/usr/bin/env python3
"""
CHIMERA DEVELOPMENT DASHBOARD
Web-based monitoring and control interface for the Chimera project.
"""

import json
import os
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, jsonify, request
import threading
import subprocess
import sys

app = Flask(__name__)

# Project root directory
PROJECT_ROOT = Path(__file__).parent
CHIMERA_DIR = PROJECT_ROOT / "Chimera"

# Data sources
TASK_BOARD_FILE = CHIMERA_DIR / "core" / "task_board_state.json"
AGENT_LOGS_DIR = PROJECT_ROOT / "agent_logs"
ORCHESTRATOR_STATUS_FILE = CHIMERA_DIR.parent / ".ORCHESTRATOR_STATUS"
BIOMEDICAL_REPORT_FILE = PROJECT_ROOT / "biomedical_pipeline_report.json"

def get_task_board_data():
    """Load task board state."""
    if TASK_BOARD_FILE.exists():
        with open(TASK_BOARD_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"tasks": [], "next_id": 0}

def get_agent_logs():
    """Get recent agent log files."""
    if AGENT_LOGS_DIR.exists():
        logs = sorted(AGENT_LOGS_DIR.glob("*.log"), key=lambda x: x.stat().st_mtime, reverse=True)
        reports = sorted(AGENT_LOGS_DIR.glob("*_report.json"), key=lambda x: x.stat().st_mtime, reverse=True)
        return {
            "logs": [str(log.name) for log in logs[:10]],
            "reports": [str(report.name) for report in reports[:10]]
        }
    return {"logs": [], "reports": []}

def get_orchestrator_status():
    """Get orchestrator status."""
    if ORCHESTRATOR_STATUS_FILE.exists():
        with open(ORCHESTRATOR_STATUS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"running": False, "paused": False}

def get_biomedical_report():
    """Get biomedical pipeline report."""
    if BIOMEDICAL_REPORT_FILE.exists():
        with open(BIOMEDICAL_REPORT_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

@app.route('/')
def dashboard():
    """Render main dashboard."""
    return render_template('dashboard.html')

@app.route('/api/status')
def api_status():
    """Get overall system status."""
    task_board = get_task_board_data()
    orchestrator = get_orchestrator_status()
    biomedical = get_biomedical_report()
    
    # Calculate metrics
    total_tasks = len(task_board.get("tasks", []))
    completed_tasks = sum(1 for t in task_board.get("tasks", []) if t.get("status") == "done")
    pending_tasks = total_tasks - completed_tasks
    
    status = {
        "timestamp": datetime.now().isoformat(),
        "orchestrator_running": orchestrator.get("running", False),
        "orchestrator_paused": orchestrator.get("paused", False),
        "task_board": {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "pending_tasks": pending_tasks,
            "completion_rate": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        },
        "biomedical_pipeline": biomedical,
        "recent_activity": get_agent_logs()
    }
    
    return jsonify(status)

@app.route('/api/tasks')
def api_tasks():
    """Get task board data."""
    task_board = get_task_board_data()
    return jsonify(task_board)

@app.route('/api/agents')
def api_agents():
    """Get agent logs and reports."""
    return jsonify(get_agent_logs())

@app.route('/api/orchestrator/<command>')
def api_orchestrator_command(command):
    """Send command to orchestrator via .ORCHESTRATOR_CMD file."""
    cmd_file = CHIMERA_DIR.parent / ".ORCHESTRATOR_CMD"
    
    try:
        # Write command to file
        cmd_file.write_text(command.lower())
        
        return jsonify({
            "success": True,
            "command": command,
            "message": f"Command '{command}' sent to orchestrator"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/biomedical')
def api_biomedical():
    """Get biomedical pipeline report."""
    report = get_biomedical_report()
    if report:
        return jsonify(report)
    return jsonify({"error": "No biomedical report found"}), 404

@app.route('/api/logs/<filename>')
def api_log_file(filename):
    """Read a log file."""
    log_path = AGENT_LOGS_DIR / filename
    
    if not log_path.exists():
        return jsonify({"error": "File not found"}), 404
    
    with open(log_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    return jsonify({
        "filename": str(filename),
        "content": content
    })

def run_dashboard():
    """Start the Flask dashboard server."""
    print("="*80)
    print("CHIMERA DEVELOPMENT DASHBOARD")
    print("="*80)
    print(f"Dashboard URL: http://localhost:5000")
    print("Press Ctrl+C to stop")
    
    # BIND LOCALHOST ONLY (fixed 2026-07-23). '0.0.0.0' means every network interface, so
    # this dashboard was reachable from any machine on the LAN. Flask's own startup banner
    # warns about this and it is easy to scroll past. The agent and the browser are both on
    # this machine; 127.0.0.1 reaches them and nothing else.
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)

if __name__ == '__main__':
    run_dashboard()
