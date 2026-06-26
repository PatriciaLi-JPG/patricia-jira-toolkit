import { Check, Eraser, Lightbulb, PencilLine, RefreshCcw, RotateCcw, Target } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import type { BoardCell } from "./game";
import {
  clearSelectedCell,
  createGame,
  digits,
  getRelatedCellIds,
  isPuzzleComplete,
  makeCellId,
  puzzles,
  revealSelectedCell,
  selectCell,
  selectPuzzle,
  setSelectedCellValue,
  toggleNote
} from "./game";

function formatTime(totalSeconds: number): string {
  const minutes = Math.floor(totalSeconds / 60)
    .toString()
    .padStart(2, "0");
  const seconds = (totalSeconds % 60).toString().padStart(2, "0");
  return `${minutes}:${seconds}`;
}

function getCellLabel(cell: BoardCell): string {
  return `Row ${cell.row + 1}, column ${cell.col + 1}${cell.value ? `, ${cell.value}` : ""}`;
}

export function App() {
  const [game, setGame] = useState(() => createGame());
  const [noteMode, setNoteMode] = useState(false);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);

  const selectedCell = useMemo(
    () => game.board.find((cell) => cell.id === game.selectedCellId) ?? game.board[0],
    [game.board, game.selectedCellId]
  );

  const relatedCellIds = useMemo(() => new Set(getRelatedCellIds(selectedCell)), [selectedCell]);
  const selectedValue = selectedCell.value;
  const filledCount = game.board.filter((cell) => cell.value !== null).length;
  const progressPercent = Math.round((filledCount / game.board.length) * 100);
  const attemptedMoves = game.board.filter((cell) => !cell.isGiven && cell.value !== null).length;
  const accuracy = attemptedMoves === 0 ? 100 : Math.max(0, Math.round(((attemptedMoves - game.mistakes) / attemptedMoves) * 100));
  const nextPuzzleId = useMemo(() => {
    const currentIndex = puzzles.findIndex((puzzle) => puzzle.id === game.puzzle.id);
    return puzzles[(currentIndex + 1) % puzzles.length].id;
  }, [game.puzzle.id]);

  useEffect(() => {
    if (game.status === "complete") {
      return;
    }

    const timer = window.setInterval(() => {
      setElapsedSeconds((current) => current + 1);
    }, 1000);

    return () => window.clearInterval(timer);
  }, [game.status]);

  const restart = useCallback(() => {
    setGame((current) => createGame(current.puzzle.id));
    setNoteMode(false);
    setElapsedSeconds(0);
  }, []);

  const changePuzzle = useCallback((puzzleId: string) => {
    setGame((current) => selectPuzzle(current, puzzleId));
    setNoteMode(false);
    setElapsedSeconds(0);
  }, []);

  const enterDigit = useCallback(
    (digit: number) => {
      setGame((current) => (noteMode ? toggleNote(current, digit) : setSelectedCellValue(current, digit)));
    },
    [noteMode]
  );

  const clearCell = useCallback(() => {
    setGame((current) => clearSelectedCell(current));
  }, []);

  const useHint = useCallback(() => {
    setGame((current) => revealSelectedCell(current));
  }, []);

  const moveSelection = useCallback((rowDelta: number, colDelta: number) => {
    setGame((current) => {
      const cell = current.board.find((candidate) => candidate.id === current.selectedCellId);
      if (!cell) {
        return current;
      }

      const row = Math.min(8, Math.max(0, cell.row + rowDelta));
      const col = Math.min(8, Math.max(0, cell.col + colDelta));
      return selectCell(current, makeCellId(row, col));
    });
  }, []);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key >= "1" && event.key <= "9") {
        event.preventDefault();
        enterDigit(Number(event.key));
      } else if (event.key === "Backspace" || event.key === "Delete" || event.key === "0") {
        event.preventDefault();
        clearCell();
      } else if (event.key === "n" || event.key === "N") {
        setNoteMode((enabled) => !enabled);
      } else if (event.key === "ArrowUp") {
        event.preventDefault();
        moveSelection(-1, 0);
      } else if (event.key === "ArrowDown") {
        event.preventDefault();
        moveSelection(1, 0);
      } else if (event.key === "ArrowLeft") {
        event.preventDefault();
        moveSelection(0, -1);
      } else if (event.key === "ArrowRight") {
        event.preventDefault();
        moveSelection(0, 1);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [clearCell, enterDigit, moveSelection]);

  return (
    <main className="app-shell">
      <section className="game-stage" aria-label="Sudoku game">
        <header className="topbar">
          <div className="title-block">
            <p className="eyebrow">Orbital Logic</p>
            <h1>Orbit Sudoku</h1>
          </div>

          <div className="metrics" aria-label="Game metrics">
            <div className="metric">
              <span>Time</span>
              <strong>{formatTime(elapsedSeconds)}</strong>
            </div>
            <div className="metric">
              <span>Filled</span>
              <strong>{filledCount}/81</strong>
            </div>
            <div className="metric">
              <span>Mistakes</span>
              <strong>{game.mistakes}</strong>
            </div>
            <div className="metric">
              <span>Streak</span>
              <strong>{game.streak}</strong>
            </div>
          </div>
        </header>

        <div className="game-layout">
          <section className="board-panel" aria-label={`${game.puzzle.title} sudoku board`}>
            <div className={`board ${game.status === "complete" ? "complete" : ""}`}>
              {game.board.map((cell) => {
                const isSelected = cell.id === game.selectedCellId;
                const isRelated = relatedCellIds.has(cell.id);
                const isConflict = game.conflictCellIds.includes(cell.id);
                const isSameValue = selectedValue !== null && cell.value === selectedValue;

                return (
                  <button
                    aria-label={getCellLabel(cell)}
                    className={[
                      "cell",
                      cell.isGiven ? "given" : "",
                      isSelected ? "selected" : "",
                      isRelated ? "related" : "",
                      isConflict ? "conflict" : "",
                      isSameValue ? "same-value" : ""
                    ]
                      .filter(Boolean)
                      .join(" ")}
                    key={cell.id}
                    onClick={() => setGame((current) => selectCell(current, cell.id))}
                    type="button"
                  >
                    {cell.value ? (
                      <span className="cell-value">{cell.value}</span>
                    ) : (
                      <span className="notes" aria-hidden="true">
                        {digits.map((digit) => (
                          <span key={digit}>{cell.notes.includes(digit) ? digit : ""}</span>
                        ))}
                      </span>
                    )}
                  </button>
                );
              })}
            </div>
          </section>

          <aside className="control-panel">
            <div className="puzzle-card">
              <label htmlFor="puzzle-select">Puzzle</label>
              <select
                id="puzzle-select"
                onChange={(event) => changePuzzle(event.target.value)}
                value={game.puzzle.id}
              >
                {puzzles.map((puzzle) => (
                  <option key={puzzle.id} value={puzzle.id}>
                    {puzzle.title}
                  </option>
                ))}
              </select>
              <div className="difficulty-row">
                <span>{game.puzzle.difficulty}</span>
                {game.status === "complete" ? (
                  <strong>
                    <Check size={16} aria-hidden="true" /> Complete
                  </strong>
                ) : (
                  <strong>{isPuzzleComplete(game) ? "Complete" : "In progress"}</strong>
                )}
              </div>
              <div className="mission-panel" aria-label="Mission progress">
                <div className="mission-row">
                  <span>
                    <Target size={15} aria-hidden="true" /> Orbit
                  </span>
                  <strong>{progressPercent}%</strong>
                </div>
                <div className="progress-track" aria-hidden="true">
                  <span style={{ width: `${progressPercent}%` }} />
                </div>
                <div className="mission-stats">
                  <span>Accuracy {accuracy}%</span>
                  <span>Best streak {game.bestStreak}</span>
                </div>
              </div>
            </div>

            <div className="number-pad" aria-label="Number pad">
              {digits.map((digit) => (
                <button
                  className={noteMode ? "note-active" : ""}
                  key={digit}
                  onClick={() => enterDigit(digit)}
                  type="button"
                >
                  {digit}
                </button>
              ))}
            </div>

            <div className="actions">
              <button
                aria-pressed={noteMode}
                className={noteMode ? "active" : ""}
                onClick={() => setNoteMode((enabled) => !enabled)}
                type="button"
              >
                <PencilLine size={18} aria-hidden="true" />
                Notes
              </button>
              <button onClick={clearCell} type="button">
                <Eraser size={18} aria-hidden="true" />
                Clear
              </button>
              <button disabled={game.hintsRemaining === 0} onClick={useHint} type="button">
                <Lightbulb size={18} aria-hidden="true" />
                Hint {game.hintsRemaining}
              </button>
              <button onClick={restart} type="button">
                <RotateCcw size={18} aria-hidden="true" />
                Reset
              </button>
              <button onClick={() => changePuzzle(nextPuzzleId)} type="button">
                <RefreshCcw size={18} aria-hidden="true" />
                Next
              </button>
            </div>
          </aside>
        </div>
      </section>
    </main>
  );
}
