# Architecture

Orbit Sudoku keeps a small static front-end architecture:

- `src/game.ts` contains deterministic Sudoku state, puzzle data, immutable
  updates, conflict detection, note handling, and completion checks.
- `src/game.test.ts` covers the game engine with Vitest.
- `src/App.tsx` renders the React game UI and owns browser-only state such as
  elapsed time and keyboard handling.
- `src/styles.css` contains the responsive visual system and board layout.
- `.gitlab-ci.yml` installs dependencies from AMS02 Nexus, runs tests and the
  production build, then publishes the Vite `dist` folder as GitLab Pages when
  enabled in the target repository.

The app is intentionally static. It has no backend, no runtime network calls,
and no persisted user data.
