# Orbit Sudoku Retrospective

## AI Tools Used

- Codex for repository inspection, implementation, documentation, testing, and
  Git operations.
- Google Docs connector for reading the challenge requirements.
- Git/GitHub for source control and sharing.

## Development Workflow

1. Read the challenge requirements from the Kira document.
2. Inspect a completed Vite/React game project for structure, scripts, testing,
   and deployment patterns.
3. Copy the useful project skeleton into a new local workspace.
4. Change the concept from the reference implementation into Orbit Sudoku.
5. Add original gameplay signals: hint budget, streak, accuracy, and orbit
   progress.
6. Expand tests for the new game-engine behavior.
7. Run tests and production build locally.
8. Push the project into a GitHub repository and publish a playable static build.

## What Worked Well

- Keeping the game engine in `src/game.ts` made AI-assisted changes easier to
  review and test.
- Vitest gave quick feedback after each logic change.
- The reference project helped with setup speed, but the new mechanics and
  visual direction kept the final game from feeling like a direct copy.
- Static hosting is a good fit for this kind of challenge because reviewers can
  play the game without local setup.

## What Did Not Work Well

- The local `npm` command hit an internal npm error in this environment.
- The public npm registry was not reachable from the company network during one
  install attempt.
- The workaround was to use the company Nexus registry and pnpm from the bundled
  Codex runtime for dependency installation, then still validate with the normal
  npm scripts.
- GitHub CLI was not installed locally, so push and repository checks used
  standard Git commands instead.

## Surprises And Discoveries

- A small game still benefits from a proper spec. It helped separate standard
  Sudoku rules from the original Orbit-specific layer.
- The "play online" requirement changes the project quality bar. A game that
  only runs locally is harder to review and demo.
- Documentation quality matters as much as code for this exercise because the
  goal is to capture reusable AI-native workflow patterns.

## Estimated Percentage Of AI-Generated Code

Approximately 70 percent of the final code and documentation was AI-generated or
AI-edited, with human direction on the goal, repository choice, differentiation
requirement, and final acceptance expectations.

## Time Spent

Estimated active time: about 1.5 to 2 hours.

This includes reading requirements, adapting the project, adding mechanics,
running tests, resolving local dependency issues, documenting the work, and
pushing to Git.

## What I Would Do Differently Next Time

- Start with the final deployment target earlier so the README link can be
  verified sooner.
- Create a screenshot or short demo clip as soon as the first playable version is
  ready.
- Decide up front whether the final submission should live in the shared GitLab
  group or a personal GitHub repository.
- Add a small end-to-end browser smoke test if time allows.

## Key Lessons Learned

- AI is strongest when the task is broken into clear, testable layers.
- A reference project is useful for architecture and setup, but the final product
  needs distinct mechanics, language, and visual identity.
- Tests are the fastest way to keep AI-generated game logic honest.
- Deployment documentation should be treated as part of the product, not an
  afterthought.
- Retrospective notes are more useful when they include friction and workarounds,
  not only success stories.
