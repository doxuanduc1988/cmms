import os
import re

TEMPLATE_DIR = 'templates'

# Cấu hình mapping thư mục -> module_code
DIR_MODULE_MAP = {
    'hr/health': 'hr.health',
    'hr/leave': 'hr.leave',
    'hr': 'hr',
    'departments': 'department',
    'job_positions': 'job_positions',
    'roles': 'roles',
    'modules': 'modules',
    'permissions': 'permissions',
    'crew': 'crew',
    'employees': 'employees',
    'attendance': 'attendance',
    'audit': 'audit_logs',
}

def get_module_code(filepath):
    rel_path = os.path.relpath(filepath, TEMPLATE_DIR)
    # Tìm longest match
    matched_module = 'unknown'
    max_len = 0
    for prefix, mod in DIR_MODULE_MAP.items():
        if rel_path.startswith(prefix) and len(prefix) > max_len:
            matched_module = mod
            max_len = len(prefix)
    return matched_module

def process_file(filepath):
    module_code = get_module_code(filepath)
    if module_code == 'unknown':
        return

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content

    # Regex to find <a> or <button> that has title="Sửa" or class includes fa-edit
    # We will look for <a ...> ... <i ... fa-edit ...> ... </a>
    # Or <button ...> ... <i ... fa-trash ...> ... </button>
    
    # A safer approach: search line by line, if a line has <a and fa-edit or fa-trash
    # Actually, often it spans multiple lines.
    # Let's use a regex that matches the whole tag block.
    
    # SỬA: <a href="{{ url_for... }}" ... title="Sửa"> ... <i class="fas fa-edit ..."></i> ... </a>
    edit_pattern = re.compile(r'(<a\s+[^>]*href=[^>]*>.*?<i\s+class="[^"]*fa-edit[^"]*"[^>]*>.*?</a>)', re.IGNORECASE | re.DOTALL)
    
    def edit_repl(match):
        block = match.group(1)
        if '{% if has_permission' in block or 'has_permission' in block:
            return block # Already wrapped
            
        # Create disabled version
        # Replace <a with <button disabled
        # Remove href
        disabled_block = re.sub(r'<a\s+href="[^"]*"\s*', '<button disabled ', block)
        # Add tooltip and classes
        disabled_block = disabled_block.replace('title="Sửa"', 'data-bs-toggle="tooltip" title="Bạn chỉ có quyền xem, không có quyền sửa"')
        if 'title=' not in disabled_block:
            # Inject it
            disabled_block = disabled_block.replace('<button disabled ', '<button disabled data-bs-toggle="tooltip" title="Bạn chỉ có quyền xem, không có quyền sửa" ')
            
        # Change color of icon to secondary
        disabled_block = re.sub(r'(fa-edit\s+)text-\w+', r'\1text-secondary', disabled_block)
        
        # Change </a> to </button>
        disabled_block = disabled_block.replace('</a>', '</button>')
        
        return f"{{% if has_permission('{module_code}', 'update') %}}\n{block}\n{{% else %}}\n{disabled_block}\n{{% endif %}}"

    content = edit_pattern.sub(edit_repl, content)
    
    # XÓA: <form ...> ... <button ... title="Xóa"> ... <i class="fas fa-trash ..."></i> ... </button> ... </form>
    delete_pattern = re.compile(r'(<form\s+[^>]*action=[^>]*>.*?<button\s+[^>]*>.*?<i\s+class="[^"]*fa-trash[^"]*"[^>]*>.*?</button>.*?</form>)', re.IGNORECASE | re.DOTALL)
    
    def delete_repl(match):
        block = match.group(1)
        if '{% if has_permission' in block or 'has_permission' in block:
            return block
            
        # Replace form action to javascript:void(0) or just render a disabled button instead of form
        # We can just render the disabled button
        btn_match = re.search(r'(<button\s+[^>]*>.*?<i\s+class="[^"]*fa-trash[^"]*"[^>]*>.*?</button>)', block, re.IGNORECASE | re.DOTALL)
        if not btn_match:
            return block
            
        btn_block = btn_match.group(1)
        disabled_btn = btn_block.replace('<button ', '<button disabled data-bs-toggle="tooltip" title="Bạn chỉ có quyền xem, không có quyền xóa" ')
        disabled_btn = re.sub(r'(fa-trash(?:-alt)?\s+)text-\w+', r'\1text-secondary', disabled_btn)
        
        return f"{{% if has_permission('{module_code}', 'delete') %}}\n{block}\n{{% else %}}\n{disabled_btn}\n{{% endif %}}"

    content = delete_pattern.sub(delete_repl, content)

    if original != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {filepath}")

for root, dirs, files in os.walk(TEMPLATE_DIR):
    for f in files:
        if f.endswith('.html'):
            process_file(os.path.join(root, f))
