export type CellId = `r${number}c${number}`;
export type GameStatus = "playing" | "complete";

export interface SudokuPuzzle {
  id: string;
  title: string;
  difficulty: "Easy" | "Medium";
  puzzle: number[][];
  solution: number[][];
}

export interface BoardCell {
  id: CellId;
  row: number;
  col: number;
  boxIndex: number;
  isGiven: boolean;
  value: number | null;
  solution: number;
  notes: number[];
}

export interface GameState {
  puzzle: SudokuPuzzle;
  board: BoardCell[];
  selectedCellId: CellId;
  conflictCellIds: CellId[];
  status: GameStatus;
  mistakes: number;
  hintsRemaining: number;
  streak: number;
  bestStreak: number;
}

export const digits = [1, 2, 3, 4, 5, 6, 7, 8, 9] as const;

export const puzzles: SudokuPuzzle[] = [
  {
    id: "morning-grid",
    title: "Morning Grid",
    difficulty: "Easy",
    puzzle: [
      [5, 3, 0, 0, 7, 0, 0, 0, 0],
      [6, 0, 0, 1, 9, 5, 0, 0, 0],
      [0, 9, 8, 0, 0, 0, 0, 6, 0],
      [8, 0, 0, 0, 6, 0, 0, 0, 3],
      [4, 0, 0, 8, 0, 3, 0, 0, 1],
      [7, 0, 0, 0, 2, 0, 0, 0, 6],
      [0, 6, 0, 0, 0, 0, 2, 8, 0],
      [0, 0, 0, 4, 1, 9, 0, 0, 5],
      [0, 0, 0, 0, 8, 0, 0, 7, 9]
    ],
    solution: [
      [5, 3, 4, 6, 7, 8, 9, 1, 2],
      [6, 7, 2, 1, 9, 5, 3, 4, 8],
      [1, 9, 8, 3, 4, 2, 5, 6, 7],
      [8, 5, 9, 7, 6, 1, 4, 2, 3],
      [4, 2, 6, 8, 5, 3, 7, 9, 1],
      [7, 1, 3, 9, 2, 4, 8, 5, 6],
      [9, 6, 1, 5, 3, 7, 2, 8, 4],
      [2, 8, 7, 4, 1, 9, 6, 3, 5],
      [3, 4, 5, 2, 8, 6, 1, 7, 9]
    ]
  },
  {
    id: "evening-grid",
    title: "Evening Grid",
    difficulty: "Medium",
    puzzle: [
      [8, 0, 0, 0, 0, 0, 0, 0, 0],
      [0, 0, 3, 6, 0, 0, 0, 0, 0],
      [0, 7, 0, 0, 9, 0, 2, 0, 0],
      [0, 5, 0, 0, 0, 7, 0, 0, 0],
      [0, 0, 0, 0, 4, 5, 7, 0, 0],
      [0, 0, 0, 1, 0, 0, 0, 3, 0],
      [0, 0, 1, 0, 0, 0, 0, 6, 8],
      [0, 0, 8, 5, 0, 0, 0, 1, 0],
      [0, 9, 0, 0, 0, 0, 4, 0, 0]
    ],
    solution: [
      [8, 1, 2, 7, 5, 3, 6, 4, 9],
      [9, 4, 3, 6, 8, 2, 1, 7, 5],
      [6, 7, 5, 4, 9, 1, 2, 8, 3],
      [1, 5, 4, 2, 3, 7, 8, 9, 6],
      [3, 6, 9, 8, 4, 5, 7, 2, 1],
      [2, 8, 7, 1, 6, 9, 5, 3, 4],
      [5, 2, 1, 9, 7, 4, 3, 6, 8],
      [4, 3, 8, 5, 2, 6, 9, 1, 7],
      [7, 9, 6, 3, 1, 8, 4, 5, 2]
    ]
  }
];

export function makeCellId(row: number, col: number): CellId {
  return `r${row}c${col}`;
}

export function getBoxIndex(row: number, col: number): number {
  return Math.floor(row / 3) * 3 + Math.floor(col / 3);
}

export function createGame(puzzleId: string = puzzles[0].id): GameState {
  const puzzle = findPuzzle(puzzleId);
  const board = createBoard(puzzle);
  const selectedCellId = findFirstEditableCell(board)?.id ?? makeCellId(0, 0);

  return {
    puzzle,
    board,
    selectedCellId,
    conflictCellIds: [],
    status: "playing",
    mistakes: 0,
    hintsRemaining: 3,
    streak: 0,
    bestStreak: 0
  };
}

export function selectPuzzle(state: GameState, puzzleId: string): GameState {
  const next = createGame(puzzleId);
  return state.puzzle.id === next.puzzle.id ? createGame(next.puzzle.id) : next;
}

export function selectCell(state: GameState, cellId: CellId): GameState {
  return getCell(state.board, cellId) ? { ...state, selectedCellId: cellId } : state;
}

export function setSelectedCellValue(state: GameState, value: number): GameState {
  if (!digits.includes(value as (typeof digits)[number])) {
    return state;
  }

  const selected = getCell(state.board, state.selectedCellId);
  if (!selected || selected.isGiven) {
    return state;
  }

  const board = state.board.map((cell) =>
    cell.id === selected.id
      ? {
          ...cell,
          value,
          notes: []
        }
      : cell
  );

  const conflictCellIds = getConflictCellIds(board);
  const isCorrect = selected.solution === value;
  const streak = isCorrect ? state.streak + 1 : 0;
  const mistakes = isCorrect ? state.mistakes : state.mistakes + 1;

  return withStatus({
    ...state,
    board,
    conflictCellIds,
    mistakes,
    streak,
    bestStreak: Math.max(state.bestStreak, streak)
  });
}

export function revealSelectedCell(state: GameState): GameState {
  const selected = getCell(state.board, state.selectedCellId);
  if (!selected || selected.isGiven || selected.value === selected.solution || state.hintsRemaining <= 0) {
    return state;
  }

  const board = state.board.map((cell) =>
    cell.id === selected.id
      ? {
          ...cell,
          value: cell.solution,
          notes: []
        }
      : cell
  );

  return withStatus({
    ...state,
    board,
    conflictCellIds: getConflictCellIds(board),
    hintsRemaining: state.hintsRemaining - 1,
    streak: 0
  });
}

export function clearSelectedCell(state: GameState): GameState {
  const selected = getCell(state.board, state.selectedCellId);
  if (!selected || selected.isGiven) {
    return state;
  }

  const board = state.board.map((cell) =>
    cell.id === selected.id
      ? {
          ...cell,
          value: null,
          notes: []
        }
      : cell
  );

  return withStatus({
    ...state,
    board,
    conflictCellIds: getConflictCellIds(board)
  });
}

export function toggleNote(state: GameState, value: number): GameState {
  if (!digits.includes(value as (typeof digits)[number])) {
    return state;
  }

  const selected = getCell(state.board, state.selectedCellId);
  if (!selected || selected.isGiven || selected.value !== null) {
    return state;
  }

  const board = state.board.map((cell) => {
    if (cell.id !== selected.id) {
      return cell;
    }

    const notes = cell.notes.includes(value)
      ? cell.notes.filter((note) => note !== value)
      : [...cell.notes, value].sort((a, b) => a - b);

    return {
      ...cell,
      notes
    };
  });

  return {
    ...state,
    board
  };
}

export function isPuzzleComplete(state: GameState): boolean {
  return state.board.every((cell) => cell.value === cell.solution) && state.conflictCellIds.length === 0;
}

export function getRelatedCellIds(cell: BoardCell): CellId[] {
  const ids: CellId[] = [];

  for (let index = 0; index < 9; index += 1) {
    ids.push(makeCellId(cell.row, index));
    ids.push(makeCellId(index, cell.col));
  }

  const boxRowStart = Math.floor(cell.row / 3) * 3;
  const boxColStart = Math.floor(cell.col / 3) * 3;
  for (let row = boxRowStart; row < boxRowStart + 3; row += 1) {
    for (let col = boxColStart; col < boxColStart + 3; col += 1) {
      ids.push(makeCellId(row, col));
    }
  }

  return [...new Set(ids)];
}

function findPuzzle(puzzleId: string): SudokuPuzzle {
  return puzzles.find((puzzle) => puzzle.id === puzzleId) ?? puzzles[0];
}

function createBoard(puzzle: SudokuPuzzle): BoardCell[] {
  return puzzle.puzzle.flatMap((rowValues, row) =>
    rowValues.map((value, col) => ({
      id: makeCellId(row, col),
      row,
      col,
      boxIndex: getBoxIndex(row, col),
      isGiven: value !== 0,
      value: value === 0 ? null : value,
      solution: puzzle.solution[row][col],
      notes: []
    }))
  );
}

function findFirstEditableCell(board: BoardCell[]): BoardCell | undefined {
  return board.find((cell) => !cell.isGiven);
}

function getCell(board: BoardCell[], cellId: CellId): BoardCell | undefined {
  return board.find((cell) => cell.id === cellId);
}

function getConflictCellIds(board: BoardCell[]): CellId[] {
  const conflictIds = new Set<CellId>();
  const units: BoardCell[][] = [];

  for (let index = 0; index < 9; index += 1) {
    units.push(board.filter((cell) => cell.row === index));
    units.push(board.filter((cell) => cell.col === index));
    units.push(board.filter((cell) => cell.boxIndex === index));
  }

  for (const unit of units) {
    for (const digit of digits) {
      const matches = unit.filter((cell) => cell.value === digit);
      if (matches.length > 1) {
        for (const match of matches) {
          conflictIds.add(match.id);
        }
      }
    }
  }

  return [...conflictIds].sort();
}

function withStatus(state: GameState): GameState {
  return {
    ...state,
    status: isPuzzleComplete(state) ? "complete" : "playing"
  };
}
