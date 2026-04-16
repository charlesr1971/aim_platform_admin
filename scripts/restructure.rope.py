import os
from rope.base.project import Project
from rope.refactor.move import create_move

PROJECT_ROOT = r'C:\inetpub\wwwroot\aim_platform_admin'

# ─── Step 1: Define the new folders ───────────────────────────────────────────

NEW_FOLDERS = ['py', 'py/imports', 'py/schedule', 'py/diagnostics']

# ─── Step 2: Define every move ────────────────────────────────────────────────

MOVES = [
    # py/imports/
    ('env_loader.py',       'py/imports'),
    ('db_utils.py',         'py/imports'),
    ('auth_gate.py',        'py/imports'),
    ('admin.py',            'py/imports'),
    ('data_engine.py',      'py/imports'),
    ('analytics_engine.py', 'py/imports'),
    ('stripe_handler.py',   'py/imports'),
    ('ui_utils.py',         'py/imports'),
    ('style_utils.py',      'py/imports'),

    # py/schedule/
    ('data_ingest.py',      'py/schedule'),
    ('discovery_engine.py', 'py/schedule'),
    ('backup_db.py',        'py/schedule'),
    ('full_name_sync.py',   'py/schedule'),

    # py/diagnostics/
    ('test_env.py',         'py/diagnostics'),
    ('test_claude.py',      'py/diagnostics'),
    ('list_models.py',      'py/diagnostics'),
    ('register_admin.py',   'py/diagnostics'),
]

# ─── Step 3: Create folders + __init__.py files ────────────────────────────────

print("Creating folders and __init__.py files...")

for folder in NEW_FOLDERS:
    folder_path = os.path.join(PROJECT_ROOT, folder)
    os.makedirs(folder_path, exist_ok=True)

    init_path = os.path.join(folder_path, '__init__.py')
    if not os.path.exists(init_path):
        open(init_path, 'w').close()
        print(f"  Created {folder}/__init__.py")
    else:
        print(f"  {folder}/__init__.py already exists, skipping.")

# ─── Step 4: Move each file with Rope (auto-updates all imports) ───────────────

print("\nMoving files and updating imports...")

proj = Project(PROJECT_ROOT)

try:
    for source_path, destination_folder in MOVES:
        try:
            resource = proj.get_resource(source_path)
            mover = create_move(proj, resource)
            changes = mover.get_changes(destination_folder)
            changes.do()
            print(f"  ✔ {source_path}  →  {destination_folder}/{source_path}")
        except Exception as e:
            print(f"  ✘ FAILED: {source_path} — {e}")
finally:
    proj.close()

print("\nDone. All files moved and imports updated.")

# ─── Step 5: Update .bat files manually ───────────────────────────────────────

print("\nUpdating .bat files...")

BAT_FOLDER = os.path.join(PROJECT_ROOT, 'bat')

# Define which script names need to change to which module paths
REPLACEMENTS = {
    "data_ingest.py":      "-m py.schedule.data_ingest",
    "discovery_engine.py": "-m py.schedule.discovery_engine",
    "backup_db.py":        "-m py.schedule.backup_db",
    "full_name_sync.py":   "-m py.schedule.full_name_sync",
    "test_env.py":         "-m py.diagnostics.test_env",
    "test_claude.py":      "-m py.diagnostics.test_claude",
    "list_models.py":      "-m py.diagnostics.list_models",
    "register_admin.py":   "-m py.diagnostics.register_admin"
}

for bat_file in os.listdir(BAT_FOLDER):
    if bat_file.endswith(".bat"):
        path = os.path.join(BAT_FOLDER, bat_file)
        
        with open(path, 'r') as f:
            content = f.read()

        new_content = content
        for old, new in REPLACEMENTS.items():
            # Replace the old 'script.py' with '-m py.path.script'
            new_content = new_content.replace(old, new)

        if new_content != content:
            with open(path, 'w') as f:
                f.write(new_content)
            print(f"  ✔ Updated: {bat_file}")
