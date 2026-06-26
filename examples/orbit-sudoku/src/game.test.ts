import { describe, expect, it } from "vitest";
import {
  clearSelectedCell,
  createGame,
  isPuzzleComplete,
  makeCellId,
  puzzles,
  revealSelectedCell,
  selectCell,
  selectPuzzle,
  setSelectedCellValue,
  toggleNote
} from "./game";

describe("sudoku game engine", () => {
  it("creates a playable board with fixed givens", () => {
    const game = createGame();

    expect(game.status).toBe("playing");
    expect(game.board).toHaveLength(81);
    expect(game.selectedCellId).toBe(makeCellId(0, 2));
    expect(game.hintsRemaining).toBe(3);
    expect(game.streak).toBe(0);
    expect(game.board.find((cell) => cell.id === makeCellId(0, 0))?.isGiven).toBe(true);
    expect(game.board.find((cell) => cell.id === makeCellId(0, 2))?.isGiven).toBe(false);
  });

  it("places a value in the selected editable cell", () => {
    const game = selectCell(createGame(), makeCellId(0, 2));
    const next = setSelectedCellValue(game, 4);

    expect(next.board.find((cell) => cell.id === makeCellId(0, 2))?.value).toBe(4);
    expect(next.status).toBe("playing");
  });

  it("tracks correct-entry streaks and resets after mistakes", () => {
    const firstCorrect = setSelectedCellValue(selectCell(createGame(), makeCellId(0, 2)), 4);
    const secondCorrect = setSelectedCellValue(selectCell(firstCorrect, makeCellId(0, 3)), 6);
    const wrong = setSelectedCellValue(selectCell(secondCorrect, makeCellId(0, 5)), 6);

    expect(firstCorrect.streak).toBe(1);
    expect(secondCorrect.streak).toBe(2);
    expect(secondCorrect.bestStreak).toBe(2);
    expect(wrong.streak).toBe(0);
    expect(wrong.bestStreak).toBe(2);
    expect(wrong.mistakes).toBe(1);
  });

  it("reveals the selected editable cell with a limited hint budget", () => {
    const game = toggleNote(selectCell(createGame(), makeCellId(0, 2)), 7);
    const hinted = revealSelectedCell(game);

    expect(hinted.board.find((cell) => cell.id === makeCellId(0, 2))?.value).toBe(4);
    expect(hinted.board.find((cell) => cell.id === makeCellId(0, 2))?.notes).toEqual([]);
    expect(hinted.hintsRemaining).toBe(2);

    const sameCellAgain = revealSelectedCell(hinted);
    expect(sameCellAgain.hintsRemaining).toBe(2);
  });

  it("does not overwrite fixed givens", () => {
    const game = selectCell(createGame(), makeCellId(0, 0));
    const next = setSelectedCellValue(game, 9);

    expect(next.board.find((cell) => cell.id === makeCellId(0, 0))?.value).toBe(5);
  });

  it("flags row, column, and box conflicts", () => {
    const rowConflict = setSelectedCellValue(selectCell(createGame(), makeCellId(0, 2)), 5);
    const colConflict = setSelectedCellValue(selectCell(createGame(), makeCellId(2, 0)), 5);
    const boxConflict = setSelectedCellValue(selectCell(createGame(), makeCellId(1, 1)), 5);

    expect(rowConflict.conflictCellIds).toContain(makeCellId(0, 0));
    expect(rowConflict.conflictCellIds).toContain(makeCellId(0, 2));
    expect(colConflict.conflictCellIds).toContain(makeCellId(0, 0));
    expect(colConflict.conflictCellIds).toContain(makeCellId(2, 0));
    expect(boxConflict.conflictCellIds).toContain(makeCellId(0, 0));
    expect(boxConflict.conflictCellIds).toContain(makeCellId(1, 1));
  });

  it("stores candidate notes without changing the cell value", () => {
    const game = selectCell(createGame(), makeCellId(0, 2));
    const next = toggleNote(game, 4);
    const selected = next.board.find((cell) => cell.id === makeCellId(0, 2));

    expect(selected?.value).toBeNull();
    expect(selected?.notes).toEqual([4]);

    const cleared = toggleNote(next, 4);
    expect(cleared.board.find((cell) => cell.id === makeCellId(0, 2))?.notes).toEqual([]);
  });

  it("clears only editable selected cells", () => {
    const game = setSelectedCellValue(selectCell(createGame(), makeCellId(0, 2)), 4);
    const cleared = clearSelectedCell(game);
    const fixedAttempt = clearSelectedCell(selectCell(createGame(), makeCellId(0, 0)));

    expect(cleared.board.find((cell) => cell.id === makeCellId(0, 2))?.value).toBeNull();
    expect(fixedAttempt.board.find((cell) => cell.id === makeCellId(0, 0))?.value).toBe(5);
  });

  it("marks the puzzle complete when the solution is filled", () => {
    let game = createGame();
    const puzzle = puzzles[0];

    for (let row = 0; row < 9; row += 1) {
      for (let col = 0; col < 9; col += 1) {
        const cell = game.board.find((candidate) => candidate.id === makeCellId(row, col));
        if (cell && !cell.isGiven) {
          game = setSelectedCellValue(selectCell(game, cell.id), puzzle.solution[row][col]);
        }
      }
    }

    expect(isPuzzleComplete(game)).toBe(true);
    expect(game.status).toBe("complete");
  });

  it("switches puzzles and resets selection and conflicts", () => {
    const conflicted = setSelectedCellValue(selectCell(createGame(), makeCellId(0, 2)), 5);
    const next = selectPuzzle(conflicted, puzzles[1].id);

    expect(next.puzzle.id).toBe(puzzles[1].id);
    expect(next.conflictCellIds).toEqual([]);
    expect(next.selectedCellId).toBe(makeCellId(0, 1));
  });
});
