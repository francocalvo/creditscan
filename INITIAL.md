# Create load modal for cc statements

**Agent:** frontend
**Status:** In progress
**Dependencies:** https://www.notion.so/2faf6e7f0572803691dbe22683966e7b

## User Story
**As a** user,
**I want** a modal to upload new credit card statements,
**So that** I can easily add new data to the system.

## Repo Notes
- The header button currently navigates to `/upload-statement` (`frontend/src/layouts/DefaultLayout.vue`), but no route/view exists yet.

## Status / Dependency
This is blocked until the backend upload workflow exists.

## UX Plan (Modal)

### Step 1: Select Card
- Dropdown for existing cards (use `useCreditCards` / already-loaded cards).

### Step 2: Upload File
- PDF-only validation
- Drag & drop + file picker

### Step 3: Processing
- Loading indicator during upload
- Show clear errors for unsupported format / extraction failure

### Step 4: Confirmation (Optional)
- If backend supports it: show extracted summary + transaction count before final save

## API Integration
Check implemented in backend!

## Acceptance Criteria
- [ ] Modal opens from header button
- [ ] Card selection works
- [ ] PDF upload works with progress/loading
- [ ] Success/error feedback displayed
- [ ] Statement appears in list after upload
