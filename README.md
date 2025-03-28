# Tic Tac Toe Web Game

A modern, interactive web-based Tic Tac Toe game built with Python Flask and featuring a sleek, responsive UI.

## Features

- User Authentication System
  - Register new accounts
  - Secure login/logout functionality
  - Personal dashboard
- Game Features
  - Interactive game board
  - Real-time gameplay
  - Score tracking

## Technologies Used

- Backend: Python Flask
- Frontend: HTML, CSS, JavaScript
- Database: MySQL
- UI Framework: Custom CSS with modern design principles

## Installation

1. Clone the repository:
   ```bash
   git clone [repository-url]
   cd tic-tac-toe
   ```
3. Install dependencies:

4. Run the application:
   ```bash
   python main.py
   ```

5. Open your browser and navigate to `http://localhost:5000`

## How to Play

1. Register an account or login if you already have one
2. Navigate to the game board from your dashboard
3. The game is played on a 3x3 grid
4. Players take turns placing their marks (X or O)
5. The first player to get 3 of their marks in a row (horizontally, vertically, or diagonally) wins
6. If all squares are filled and no player has won, the game is a draw

## Project Structure

```
tic-tac-toe/
├── main.py              # Main application file
├── templates/           # HTML templates
│   ├── base.html        # Base template with common styling
│   ├── dashboard.html   # User dashboard
│   ├── home.html       # Home page
│   ├── login.html      # Login page
│   ├── register.html   # Registration page
│   └── tictactoe_play.html  # Game board
└── README.md           # Project documentation
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
