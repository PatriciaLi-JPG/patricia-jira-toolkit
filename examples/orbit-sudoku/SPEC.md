# Orbit Sudoku Spec

## Goal

Build a polished static Sudoku game with enough original gameplay and visual
direction to stand apart from the reference project.

## Core Requirements

- Render a 9x9 Sudoku board immediately on first load.
- Support selecting cells by pointer and keyboard arrows.
- Support entering digits 1-9 into editable cells.
- Prevent fixed givens from being modified.
- Support candidate notes for empty editable cells.
- Support a limited hint budget for revealing selected editable cells.
- Track streak, accuracy, and completion progress.
- Support clearing editable cells.
- Highlight the selected cell, related row/column/box cells, matching values,
  and duplicate conflicts.
- Mark the puzzle complete only when every cell matches the solution and there
  are no conflicts.
- Include at least two built-in puzzles.
- Build with Vite and publish `dist` through GitLab Pages.

## Non-Goals

- No generated puzzles.
- No backend storage.
- No account or leaderboard features.
