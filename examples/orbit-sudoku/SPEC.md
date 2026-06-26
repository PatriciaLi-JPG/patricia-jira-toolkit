# Orbit Sudoku Specification

## Objective

Build a complete, playable browser puzzle game for the AI-Native Development
Challenge. The game should be small enough to finish quickly, but complete enough
to show the full lifecycle: requirements, implementation, tests, documentation,
iteration, and deployment.

## Game Rules

Orbit Sudoku follows standard 9x9 Sudoku rules:

- The board has 9 rows, 9 columns, and 9 three-by-three boxes.
- Each row must contain digits 1 through 9 exactly once.
- Each column must contain digits 1 through 9 exactly once.
- Each three-by-three box must contain digits 1 through 9 exactly once.
- Fixed givens are part of the puzzle and cannot be edited.
- Editable cells can contain one final digit or candidate notes.
- The puzzle is complete only when every editable cell matches the solution and
  there are no row, column, or box conflicts.

## Original Game Layer

To distinguish the project from a basic Sudoku implementation, the game adds an
orbital mission layer:

- Orbit progress: percentage of filled cells.
- Accuracy: rough success rate based on filled editable cells and mistakes.
- Current streak: consecutive correct final entries.
- Best streak: highest streak in the current puzzle.
- Hint budget: three hints per puzzle, each revealing the selected editable cell.

These features make the player experience more like a focused calibration
challenge than a generic number grid.

## Scope

In scope:

- Static browser game.
- React UI.
- TypeScript game engine.
- Two built-in puzzles.
- Keyboard and pointer interaction.
- Candidate note mode.
- Conflict detection.
- Limited hints.
- Progress, accuracy, and streak feedback.
- Unit tests for game-state behavior.
- Static deployment through GitHub Pages or another static host.

Out of scope:

- User accounts.
- Backend persistence.
- Generated Sudoku puzzles.
- Leaderboards.
- Multiplayer.
- Save/resume across browser sessions.

## Functional Requirements

- Render a playable 9x9 board immediately after page load.
- Select a default editable cell when a puzzle starts.
- Allow cell selection by mouse or touch.
- Allow movement with arrow keys.
- Allow number entry with keyboard digits `1` through `9`.
- Allow clearing selected editable cells with Clear, Backspace, Delete, or `0`.
- Prevent edits to fixed givens.
- Toggle candidate note mode through the UI and `N` key.
- Add and remove candidate notes from empty editable cells.
- Clear notes when a final value is entered.
- Highlight selected, related, matching-value, and conflicting cells.
- Count mistakes when a wrong final digit is entered.
- Track current and best correct-entry streak.
- Reveal selected editable cells with the hint action while hints remain.
- Stop the timer when the puzzle is complete.
- Reset puzzle state when restarting or switching puzzles.
- Build successfully as a static Vite app.

## Acceptance Criteria

- A new user can open the published link and play without cloning the repository.
- A local developer can run `npm install`, `npm run dev`, `npm test`, and
  `npm run build`.
- All unit tests pass.
- Fixed cells cannot be changed or cleared.
- Duplicate values in a row, column, or box are visibly flagged.
- A solved board changes the game status to complete.
- Hint usage decreases the hint budget and fills the selected editable cell.
- The README includes setup, run, test, build, repository, and play-online
  instructions.
- Documentation includes README, SPEC, ARCHITECTURE, and RETROSPECTIVE files.
