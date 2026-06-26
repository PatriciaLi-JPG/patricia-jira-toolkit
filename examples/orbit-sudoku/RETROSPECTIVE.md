# Retrospective

This repository was adapted from a small Vite/React browser game architecture.
The useful parts were the static deployment shape, deterministic game engine,
Vitest coverage, and GitLab Pages pipeline.

For this Sudoku version, the old sprite and animation-heavy gameplay were
removed in favor of a board-first puzzle UI. The main project-specific CI
adjustments are:

- Use the AGS runner tags available to this GitLab project.
- Use `nexus3.int.rclabenv.com/ringcentral/web-tools:node20-openjdk17-alpine`
  so the Kubernetes runner does not need Docker Hub.
- Use the AMS02 Lab Nexus npm registry for `npm ci`.
