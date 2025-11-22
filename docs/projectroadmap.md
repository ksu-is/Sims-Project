# Project Roadmap – Sims 4 Mod Manager

_Current status: Core backup + organize flow is working as intended._

---

## Phase 0 – Setup & Planning

- [x] Create GitHub repository in KSU-IS organization
- [x] Add `mod_manager.py` starter script
- [x] Create `projectroadmap.md` to track tasks
- [ ] Add basic README with project description and how to run the script

---

## Phase 1 – Core Functionality (Current Code)

### 1. Mods Folder Selection

- [x] Allow passing Mods folder path as a command-line argument  
  - Implemented in `main()` using `sys.argv` and `Path`.
- [x] Add Tkinter folder picker to select Mods folder via GUI  
  - Implemented in `pick_mods_folder()` with `filedialog.askdirectory`.
- [x] Validate that the selected path exists and is not empty  
  - Prints a friendly error and usage example if the path is invalid.

### 2. Backup System

- [x] Create `_Backup` folder inside the Mods directory if it does not exist  
- [x] Generate timestamped backup folder names  
  - Implemented in `get_timestamp()` using `datetime.now()`.
- [x] Copy Mods contents into `_Backup/Mods_Backup_<timestamp>`  
- [x] Ignore manager-created folders during backup  
  - Skips `_Backup`, `_Organized`, `_Quarantine`, `_Duplicates`, `_Reports`.

### 3. Basic Mod Organization

- [x] Define constants for file types  
  - `SCRIPT_EXT = ".ts4script"`  
  - `PACKAGE_EXT = ".package"`
- [x] Create `_Organized` folder structure:
  - `_Organized/Script_Mods`
  - `_Organized/Package_CC`
  - `_Organized/Other`
- [x] Walk the Mods folder and organize files by type  
  - `.ts4script` → `_Organized/Script_Mods`  
  - `.package` → `_Organized/Package_CC`  
  - everything else → `_Organized/Other`
- [x] Skip special folders during organizing  
  - Ignores `_Backup`, `_Organized`, `_Quarantine`, `_Duplicates`, `_Reports`.
- [x] Print summary of what was moved  
  - Shows counts for script mods, package files, and other files.

---

## Phase 2 – Quality & Safety (Planned)

- [ ] Detect zero-byte or unreadable files and move them into `_Quarantine`
- [ ] Add basic logging or print statements when suspicious files are quarantined
- [ ] Add simple checks to avoid moving temporary/system files
- [ ] Add option to “dry-run” (show what would be moved without actually moving files)

---

## Phase 3 – Reporting & User Experience (Planned)

- [ ] Create a `_Reports` folder for logs and summaries
- [ ] Save a text report with counts of files moved and any errors
- [ ] (Optional) Save a JSON report for future tooling or analysis
- [ ] Improve console messages to be more user-friendly and step-based

---

## Phase 4 – Stretch Features (Future Ideas)

- [ ] Duplicate mod detection using file hashes (e.g., SHA-256)
- [ ] Simple Tkinter GUI window with buttons (Backup, Organize, View Report)
- [ ] Settings file (e.g., JSON) to let users customize which folders or extensions to ignore
- [ ] Detect likely Sims 4 Mods folder automatically on common paths

---

## Progress Log

- [x] Sprint 1: Folder selection, path validation, and backup implemented.
- [x] Sprint 2 (partial): Organizing mods by type into `_Organized` folders.
- [ ] Next: Add quarantine behavior and reporting for Sprint 2 completion.
