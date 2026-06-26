# Orbit Sudoku

Orbit Sudoku is a small browser puzzle game built for the AI-Native Development
Challenge. It uses classic Sudoku rules, but presents the puzzle as an "orbital
calibration" board with progress, accuracy, streak, and limited hint feedback.

The goal is to feel different from a plain Sudoku clone: the player is not just
filling numbers, they are trying to complete a clean orbit with as few course
corrections as possible.

## Play Online

Play the latest published version here:

[https://patriciali-jpg.github.io/sm-codex-toolkit/](https://patriciali-jpg.github.io/sm-codex-toolkit/)

## Git Repository

Source code:

[https://github.com/PatriciaLi-JPG/sm-codex-toolkit/tree/master/examples/orbit-sudoku](https://github.com/PatriciaLi-JPG/sm-codex-toolkit/tree/master/examples/orbit-sudoku)

## Game Description

The game starts with one of two built-in Sudoku puzzles. Fixed givens cannot be
changed. The player selects editable cells, enters digits, tracks candidate
notes, and uses up to three hints when stuck.

Orbit Sudoku adds a few game-layer signals on top of standard Sudoku:

- Orbit progress shows how much of the board has been filled.
- Accuracy estimates how cleanly the player is solving the board.
- Streak rewards consecutive correct entries.
- Hint budget creates a small resource-management choice.
- Row, column, box, same-value, and conflict highlighting keep the board easy to scan.

## Screenshots

Run the game locally or open the published link above to see the responsive game
board. The UI is intentionally board-first: the Sudoku grid is the main screen,
with compact controls beside or below it depending on viewport size.

## Setup

Install dependencies from the project directory:

```bash
npm install
```

If the public npm registry is not reachable from the company network, use the
internal Nexus registry:

```bash
npm config set registry https://nexus.int.rclabenv.com/nexus/content/groups/npm-all/
npm install
```

## Run Locally

```bash
npm run dev
```

Then open the local URL printed by Vite, usually:

```text
http://127.0.0.1:5173/
```

## Test

```bash
npm test
```

## Build

```bash
npm run build
```

For static hosting with relative asset paths:

```bash
npm run build:pages
```

## How Others Can Play

1. Open the online game link in the Play Online section.
2. Pick a puzzle from the dropdown.
3. Click a cell or move with the arrow keys.
4. Type digits `1` through `9` to fill cells.
5. Press `N` or click Notes to add candidates instead of final answers.
6. Use Hint only when needed; there are three hints per puzzle.
7. Finish the orbit by filling every cell with the correct solution.
