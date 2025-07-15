from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import os
from datetime import datetime
import json

app = FastAPI(title="Telegram Tic-Tac-Toe Mini App")

# Game state storage (in production, use a database)
games = {}


class GameState(BaseModel):
    board: List[str]
    current_player: str
    winner: Optional[str]
    game_over: bool
    created_at: datetime


class MoveRequest(BaseModel):
    game_id: str
    position: int
    player: str


class GameResponse(BaseModel):
    game_id: str
    board: List[str]
    current_player: str
    winner: Optional[str]
    game_over: bool
    message: str


def check_winner(board):
    """Check if there's a winner in the current board state"""
    winning_combinations = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8],  # rows
        [0, 3, 6], [1, 4, 7], [2, 5, 8],  # columns
        [0, 4, 8], [2, 4, 6]  # diagonals
    ]

    for combo in winning_combinations:
        if (board[combo[0]] == board[combo[1]] == board[combo[2]]
                and board[combo[0]] != ''):
            return board[combo[0]]

    # Check for tie
    if '' not in board:
        return 'tie'

    return None


def create_new_game():
    """Create a new game instance"""
    return GameState(
        board=[''] * 9,
        current_player='X',
        winner=None,
        game_over=False,
        created_at=datetime.now()
    )


@app.get("/")
async def read_root():
    return {"message": "Telegram Tic-Tac-Toe Mini App API"}


@app.post("/api/new-game")
async def new_game():
    """Create a new game"""
    game_id = f"game_{len(games) + 1}_{int(datetime.now().timestamp())}"
    games[game_id] = create_new_game()

    return GameResponse(
        game_id=game_id,
        board=games[game_id].board,
        current_player=games[game_id].current_player,
        winner=games[game_id].winner,
        game_over=games[game_id].game_over,
        message="New game created!"
    )


@app.get("/api/game/{game_id}")
async def get_game(game_id: str):
    """Get current game state"""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")

    game = games[game_id]
    return GameResponse(
        game_id=game_id,
        board=game.board,
        current_player=game.current_player,
        winner=game.winner,
        game_over=game.game_over,
        message="Game state retrieved"
    )


@app.post("/api/move")
async def make_move(move: MoveRequest):
    """Make a move in the game"""
    if move.game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")

    game = games[move.game_id]

    if game.game_over:
        raise HTTPException(status_code=400, detail="Game is already over")

    if move.position < 0 or move.position > 8:
        raise HTTPException(status_code=400, detail="Invalid position")

    if game.board[move.position] != '':
        raise HTTPException(status_code=400, detail="Position already taken")

    if move.player != game.current_player:
        raise HTTPException(status_code=400, detail="Not your turn")

    # Make the move
    game.board[move.position] = move.player

    # Check for winner
    winner = check_winner(game.board)
    if winner:
        game.winner = winner
        game.game_over = True
        if winner == 'tie':
            message = "It's a tie!"
        else:
            message = f"Player {winner} wins!"
    else:
        # Switch players
        game.current_player = 'O' if game.current_player == 'X' else 'X'
        message = f"Player {game.current_player}'s turn"

    return GameResponse(
        game_id=move.game_id,
        board=game.board,
        current_player=game.current_player,
        winner=game.winner,
        game_over=game.game_over,
        message=message
    )


@app.get("/game", response_class=HTMLResponse)
async def serve_game():
    """Serve the game HTML page"""
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tic-Tac-Toe</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/axios/dist/axios.min.js"></script>
    <style>
        body {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .game-board {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 4px;
            background: rgba(255, 255, 255, 0.1);
            padding: 8px;
            border-radius: 12px;
            backdrop-filter: blur(10px);
        }
        .cell {
            aspect-ratio: 1;
            background: rgba(255, 255, 255, 0.9);
            border: none;
            border-radius: 8px;
            font-size: 2rem;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .cell:hover:not(:disabled) {
            background: rgba(255, 255, 255, 1);
            transform: scale(1.05);
        }
        .cell:disabled {
            cursor: not-allowed;
            opacity: 0.7;
        }
        .cell.x {
            color: #e74c3c;
        }
        .cell.o {
            color: #3498db;
        }
        .winner {
            animation: pulse 1s infinite;
        }
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }
    </style>
</head>
<body class="flex items-center justify-center min-h-screen p-4">
    <div class="max-w-md w-full bg-white/10 backdrop-blur-lg rounded-xl p-6 shadow-2xl">
        <div class="text-center mb-6">
            <h1 class="text-3xl font-bold text-white mb-2">Tic-Tac-Toe</h1>
            <p id="status" class="text-white/80">Loading...</p>
        </div>

        <div id="gameBoard" class="game-board mb-6">
            <!-- Game cells will be generated here -->
        </div>

        <div class="flex gap-4">
            <button id="newGameBtn" class="flex-1 bg-green-500 hover:bg-green-600 text-white font-bold py-3 px-6 rounded-lg transition-colors">
                New Game
            </button>
            <button id="resetBtn" class="flex-1 bg-red-500 hover:bg-red-600 text-white font-bold py-3 px-6 rounded-lg transition-colors">
                Reset
            </button>
        </div>

        <div class="mt-4 text-center text-white/60 text-sm">
            <p>Player X starts first</p>
        </div>
    </div>

    <script>
        class TicTacToeGame {
            constructor() {
                this.gameId = null;
                this.currentPlayer = 'X';
                this.gameOver = false;
                this.board = Array(9).fill('');
                this.init();
            }

            init() {
                this.createBoard();
                this.bindEvents();
                this.newGame();
            }

            createBoard() {
                const gameBoard = document.getElementById('gameBoard');
                gameBoard.innerHTML = '';

                for (let i = 0; i < 9; i++) {
                    const cell = document.createElement('button');
                    cell.className = 'cell';
                    cell.dataset.index = i;
                    cell.addEventListener('click', () => this.makeMove(i));
                    gameBoard.appendChild(cell);
                }
            }

            bindEvents() {
                document.getElementById('newGameBtn').addEventListener('click', () => this.newGame());
                document.getElementById('resetBtn').addEventListener('click', () => this.resetGame());
            }

            async newGame() {
                try {
                    const response = await axios.post('/api/new-game');
                    this.gameId = response.data.game_id;
                    this.updateGameState(response.data);
                } catch (error) {
                    console.error('Error creating new game:', error);
                    this.updateStatus('Error creating new game');
                }
            }

            async makeMove(position) {
                if (this.gameOver || this.board[position] !== '') {
                    return;
                }

                try {
                    const response = await axios.post('/api/move', {
                        game_id: this.gameId,
                        position: position,
                        player: this.currentPlayer
                    });

                    this.updateGameState(response.data);
                } catch (error) {
                    console.error('Error making move:', error);
                    this.updateStatus('Error making move');
                }
            }

            updateGameState(gameData) {
                this.board = gameData.board;
                this.currentPlayer = gameData.current_player;
                this.gameOver = gameData.game_over;

                this.updateBoard();
                this.updateStatus(gameData.message);
            }

            updateBoard() {
                const cells = document.querySelectorAll('.cell');
                cells.forEach((cell, index) => {
                    cell.textContent = this.board[index];
                    cell.disabled = this.board[index] !== '' || this.gameOver;

                    // Add styling classes
                    cell.classList.remove('x', 'o', 'winner');
                    if (this.board[index] === 'X') {
                        cell.classList.add('x');
                    } else if (this.board[index] === 'O') {
                        cell.classList.add('o');
                    }

                    if (this.gameOver) {
                        cell.classList.add('winner');
                    }
                });
            }

            updateStatus(message) {
                document.getElementById('status').textContent = message;
            }

            resetGame() {
                this.gameId = null;
                this.currentPlayer = 'X';
                this.gameOver = false;
                this.board = Array(9).fill('');
                this.updateBoard();
                this.updateStatus('Click "New Game" to start');
            }
        }

        // Initialize the game when the page loads
        document.addEventListener('DOMContentLoaded', () => {
            new TicTacToeGame();
        });
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=80)
