# Orbit Sudoku

A browser Sudoku game built with Vite, React, TypeScript, and Vitest.

## Play Online

After the GitLab Pages pipeline succeeds, open the live deployment from your
repository's Pages environment.

## Game Features

- Two built-in puzzles
- 9x9 playable Sudoku board with fixed givens and editable cells
- Row, column, box, and matching-number highlighting
- Conflict detection for duplicate values
- Candidate note mode
- Three-use hint system that reveals the selected editable cell
- Streak, accuracy, and orbit-progress feedback
- Clear, reset, and next-puzzle controls
- Keyboard support for digits, clearing, notes, and grid movement
- Responsive layout for desktop and mobile

## Setup

```bash
npm install
```

## Run

```bash
npm run dev
```

Then open the local URL printed by Vite.

## Test

```bash
npm test
```

## Build

```bash
npm run build
```

For GitLab Pages, the pipeline runs:

```bash
npm run build:pages
```

The Pages build uses Vite's relative base path so assets load correctly from a
project-specific Pages domain.
