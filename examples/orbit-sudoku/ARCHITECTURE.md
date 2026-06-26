# Orbit Sudoku Architecture

## Technology Stack

- Vite for the local dev server and static production build.
- React for UI rendering and browser event handling.
- TypeScript for typed game-state logic.
- Vitest for unit tests.
- Lucide React for interface icons.
- GitHub Pages for one-click playable hosting.

## Architecture Overview

Orbit Sudoku is a static front-end app. It has no backend, no database, no
runtime API calls, and no persisted player data.

The code is intentionally split into a deterministic game engine and a browser UI:

- `src/game.ts` contains puzzle data, game state, immutable update functions,
  conflict detection, hint behavior, note behavior, streak tracking, and
  completion checks.
- `src/game.test.ts` tests the game engine without rendering React.
- `src/App.tsx` owns browser-facing state such as elapsed time, selected puzzle,
  keyboard handling, button handlers, and board rendering.
- `src/styles.css` defines the responsive layout, visual theme, board states, and
  control styling.
- `src/main.tsx` mounts the React app.

This separation made it easier to use AI assistance safely: the rules could be
tested in isolation before UI polish was added.

## Major Design Decisions

- Use Sudoku instead of a card game because it is small, familiar, and easy to
  validate with deterministic tests.
- Keep puzzle data local so the game works offline after the static page loads.
- Keep the game engine pure and immutable so actions are easy to test.
- Add Orbit-specific progress, accuracy, streak, and hint signals so the project
  feels distinct from the reference game and from a generic Sudoku board.
- Use a restrained board-first UI instead of a marketing-style landing page.
- Use relative build assets for static hosting compatibility.

## Deployment Design

The app can be hosted by any static file server. For this repository, the
playable build is published through GitHub Pages.

The publishing flow is:

1. Install dependencies.
2. Run tests.
3. Build with `npm run build:pages`.
4. Publish the generated `dist` directory as the static site.

The expected public URL is:

[https://patriciali-jpg.github.io/sm-codex-toolkit/](https://patriciali-jpg.github.io/sm-codex-toolkit/)

## AI Tooling Used

- Codex was used to inspect the reference project, plan changes, implement the
  game variation, update documentation, run tests, build the project, and push to
  Git.
- Google Docs connector was used to read the challenge requirements.
- Git was used for local version control and pushing to GitHub.

## Agent Workflow

1. Read the challenge document and extract deliverables.
2. Inspect the reference project structure and test setup.
3. Create a separate remix rather than modifying the source repository.
4. Add original game-layer behavior: hints, streaks, accuracy, and orbit progress.
5. Update tests to cover the new behavior.
6. Update documentation to match the challenge requirements.
7. Run tests and production build.
8. Push source code and deployment branch to GitHub.

## Quality Strategy

- Unit tests cover game-engine behavior such as board creation, fixed givens,
  conflict detection, note handling, clearing, puzzle completion, puzzle
  switching, streak tracking, and hint behavior.
- TypeScript build catches type and module errors.
- Vite production build verifies static hosting readiness.
