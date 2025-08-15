# LLM File Organizer - Safety Features

This document details the comprehensive safety measures built into the LLM File Organizer to protect your files and prevent data loss.

## 🛡️ Core Safety Principles

1. **Never Delete Files**: The system cannot and will not delete any files
2. **Never Overwrite Files**: Automatic conflict resolution prevents accidental overwrites  
3. **Sandbox Operation**: All operations restricted to specified directory
4. **Comprehensive Logging**: Every action is logged for audit and recovery
5. **Fail-Safe Design**: When in doubt, the system refuses to act

## 🔒 Overwrite Protection (NEW)

### Problem Solved
File move operations could accidentally overwrite existing files, causing permanent data loss.

### Solution: Automatic Conflict Resolution
- **Detection**: System checks for file conflicts before any move operation
- **Auto-Rename**: Conflicting files are automatically renamed using safe patterns
- **Preservation**: Original files are never touched or overwritten
- **Notification**: User is informed of all conflict resolutions

### Examples

#### File Conflict Resolution
```
Scenario: Moving "report.pdf" to a folder that already contains "report.pdf"

Before:
├── source/
│   └── report.pdf (new file to move)
└── destination/
    └── report.pdf (existing file)

After Move:
├── source/ (empty)
└── destination/
    ├── report.pdf (original, unchanged)
    └── report (1).pdf (moved file, auto-renamed)

Result: Both files preserved, no data loss
```

#### Directory Conflict Resolution
```
Scenario: Moving "Photos" directory to location with existing "Photos" directory

Before:
├── source/
│   └── Photos/ (contains vacation pics)
└── destination/
    └── Photos/ (contains family pics)

After Move:
├── source/ (empty)
└── destination/
    ├── Photos/ (original family pics, unchanged)
    └── Photos (1)/ (vacation pics, auto-renamed)

Result: Both photo collections preserved separately
```

### Naming Convention
- First conflict: `filename (1).ext`
- Second conflict: `filename (2).ext`
- Continues up to: `filename (9999).ext`
- Fallback: `filename_[timestamp].ext`

## 🔐 Path Security

### Directory Traversal Prevention
- All paths validated against root directory
- `../` and `..\\` patterns blocked
- Absolute paths outside root rejected
- Symbolic link attacks prevented

### System Directory Protection
**Windows Protected Paths:**
- `C:\Windows\`
- `C:\Program Files\`
- `C:\Program Files (x86)\`
- `C:\System32\`

**Unix Protected Paths:**
- `/bin/`, `/sbin/`, `/usr/bin/`, `/usr/sbin/`
- `/etc/`, `/sys/`, `/proc/`, `/dev/`, `/boot/`

### Validation Examples
```bash
# ✅ ALLOWED
python main.py --root-path "/Users/john/Documents/MyFiles"
python main.py --root-path "C:\Users\John\Downloads"

# ❌ BLOCKED
python main.py --root-path "/etc"           # System directory
python main.py --root-path "C:\Windows"     # System directory
python main.py --root-path "/nonexistent"   # Doesn't exist
```

## 📊 Comprehensive Logging

### Log Types
1. **Main Application Log**: General operations and errors
2. **Conversation Log**: Complete user interactions (JSONL format)
3. **Action Log**: Detailed filesystem operations (JSONL format)  
4. **Security Log**: Safety events and blocked actions (JSONL format)

### Safety Event Logging
All safety-related events are automatically logged:

```json
{
  "timestamp": "2024-08-14T17:17:08",
  "event_type": "FILE_CONFLICT_RESOLVED",
  "severity": "WARNING", 
  "details": {
    "original_destination": "documents/report.pdf",
    "auto_renamed_to": "documents/report (1).pdf",
    "reason": "Destination file already existed"
  }
}
```

### Log Analysis
```bash
# Check for safety events
grep -i "conflict\|overwrite\|auto-rename" logs/organizer_*.log

# View security events
cat logs/security_*.jsonl | jq '.event_type'

# Check move operations
cat logs/actions_*.jsonl | jq 'select(.action=="move_file")'
```

## 🚨 Input Validation

### Dangerous Pattern Detection
The system scans all user input for potentially dangerous patterns:

- Path traversal: `../`, `..\`, `/..`, `\..\`
- Shell injection: `;`, `|`, `&`, `` ` ``, `$()`
- System commands: `rm -rf`, `del /s`, `format`, `sudo`
- Permission changes: `chmod 777`

### Example Blocked Inputs
```
❌ "Move ../../../etc/passwd to safe/"
❌ "Rename file.txt to `rm -rf /`"  
❌ "Create directory; sudo rm -rf /"
❌ "Move file to C:\Windows\System32\"
```

## ⚙️ Safety Configuration

### Default Settings (Recommended)
```python
auto_rename = True          # Automatically resolve file conflicts
strict_mode = False         # Allow operations with safety measures
preview_mode = False        # Execute operations immediately
logging_level = "INFO"      # Log all operations
```

### Strict Mode (Maximum Safety)
```python
auto_rename = False         # Fail if any conflicts detected
strict_mode = True          # Require explicit confirmation
preview_mode = True         # Show preview before execution
logging_level = "DEBUG"     # Log everything including debug info
```

## 🧪 Safety Testing

### Automated Tests
Run comprehensive safety tests:

```bash
# Test overwrite protection
python test_overwrite_protection.py

# Test path validation  
python test_path_security.py

# Test all safety features
python test_safety_suite.py
```

### Manual Safety Verification
1. **Create test environment** with duplicate filenames
2. **Attempt moves** that would cause conflicts
3. **Verify** original files remain unchanged
4. **Check logs** for proper conflict resolution
5. **Confirm** auto-renamed files have correct content

## 🚑 Recovery Procedures

### If Something Goes Wrong

1. **Check Logs Immediately**
   ```bash
   # Latest session logs
   tail -f logs/organizer_[latest].log
   
   # All actions taken
   cat logs/actions_[latest].jsonl | jq '.'
   ```

2. **Identify What Happened**
   - Look for `ERROR` or `WARNING` entries
   - Check `auto-rename` operations
   - Verify `success: true/false` in action logs

3. **Recovery Actions**
   - Auto-renamed files can be manually renamed back
   - Check `final_path` in logs to find moved files
   - All original files should be preserved

### Emergency Stop
If needed, the system can be safely interrupted:
- `Ctrl+C` during operation
- All completed moves are logged
- Partial operations are rolled back when possible
- No files should be lost or corrupted

## 📋 Safety Checklist

Before using the LLM File Organizer:

- [ ] **Backup Important Data**: Always have backups of critical files
- [ ] **Test in Safe Environment**: Try with copies of files first
- [ ] **Choose Appropriate Root**: Select a specific folder, not system directories
- [ ] **Review Logs**: Check logs after operations for any issues
- [ ] **Understand Auto-Rename**: Know that conflicts will be auto-resolved
- [ ] **Keep Logs**: Retain log files for audit and recovery purposes

## 🎯 Best Practices

### Safe Usage Patterns
```bash
# ✅ Good: Specific project folder
python main.py --root-path "~/Projects/FileOrganization"

# ✅ Good: Downloads folder cleanup  
python main.py --root-path "~/Downloads"

# ❌ Risky: Entire home directory
python main.py --root-path "~/"

# ❌ Dangerous: System directories
python main.py --root-path "/"
```

### Safe Commands
```
# ✅ Safe informational queries
"What files are in this directory?"
"Show me the structure of this folder"

# ✅ Safe with auto-protection
"Move all PDFs to Documents folder"
"Organize photos by year"

# ✅ Safe previews
"Show me what would happen if I moved these files"
```

## 🔍 Monitoring and Alerts

### Log Monitoring
Set up monitoring for safety events:

```bash
# Watch for conflicts in real-time
tail -f logs/organizer_*.log | grep -i "conflict\|auto-rename"

# Daily safety report
grep -c "WARNING\|ERROR" logs/organizer_$(date +%Y%m%d)*.log
```

### Success Indicators
- All operations complete with `"success": true`
- No `ERROR` level log entries
- Expected number of files moved/renamed
- Auto-rename notifications for any conflicts

---

**Remember**: The LLM File Organizer is designed to be safe by default. When in doubt, it will preserve your files rather than risk data loss. All operations are logged and can be audited for compliance and recovery purposes.