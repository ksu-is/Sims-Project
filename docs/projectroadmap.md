# Project Roadmap – Sims 4 Mod Manager

## Phase 1 – Core Functionality

- [x] Create initial project structure (src folder, README, roadmap)
- [x] Add script to select Mods folder and validate path
- [x] Implement backup system to `_Backup/Mods_Backup_<timestamp>`
- [ ] Scan all files in Mods folder and collect stats
- [ ] Sort `.ts4script` into `Script_Mods` and `.package` into `Package_CC`
- [ ] Move all other file types into `Other` folder inside `_Organized`

## Phase 2 – Quality & Safety

- [ ] Detect zero-byte or unreadable files and move them to `_Quarantine`
- [ ] Detect duplicate mods using SHA256 hashing and move copies to `_Duplicates`
- [ ] Add basic error handling and user feedback messages
- [ ] Log all actions into an internal list for reporting

## Phase 3 – Reporting & UX

- [ ] Generate JSON report with stats and actions in `_Reports`
- [ ] Generate human-readable text report in `_Reports`
- [ ] Add console messages summarizing what happened
- [ ] (Stretch) Add Tkinter-based GUI for non-technical users

## Phase 4 – Stretch Goals

- [ ] Settings file to customize ignore folders and thresholds
- [ ] Dry-run mode to show actions without moving files
- [ ] Possible future integration with mod update sources
