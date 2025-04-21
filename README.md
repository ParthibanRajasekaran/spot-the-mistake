# Spot The Mistake

An interactive, web‑based puzzle game where the player must spot a subtle rotation in a grid of characters. 

---

## Table of Contents

- [Features](#features)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Running the App](#running-the-app)
- [Configuration](#configuration)
- [Usage](#usage)
- [Customization](#customization)
- [Folder Structure](#folder-structure)
- [Contributing](#contributing)
- [License](#license)

---

## Features

- **Dynamic Grid**: Automatically scales to 80% of the viewport.
- **Randomized Puzzles**: Each new game rotates one character by 10°–25°.
- **Decoy Animations**: Subtle vertical shifts in random cells to add visual noise.
- **Matrix Rain**: Full‑screen canvas rain effect upon success.
- **Typing Reveal**: Hacker‑style typewriter effect for the final message.
- **Answer Highlight**: Highlights the rotated cell in blue when you click **Answer**.

---

## Getting Started

### Prerequisites

- Python 3.8+ installed
- `pip` package manager

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/ParthibanRajasekaran/spot-the-mistake.git
   cd spot-the-mistake
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate    # macOS/Linux
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

### Running the App

Start the Flask development server:
```bash
export FLASK_APP=app.py; export FLASK_ENV=development
flask run
```

Open your browser to `http://127.0.0.1:5000`.

---

## Configuration

All key settings live at the top of `app.py`:

```python
rows, cols    = 20, 20     # grid dimensions
rot_min, rot_max = 10, 25  # rotation range in degrees
decoys = 12                # number of decoy shifts
```  

Adjust these values to change the difficulty or layout.

---

## Usage

1. Click **Generate** to create a new puzzle.
2. Scan the grid for the subtly rotated character.
3. Click **Answer** to highlight the cell and display the hint.
4. Click the highlighted cell to trigger the Matrix rain and final message.

---

## Customization

- **Grid Size**: The grid auto‑scales via CSS `--grid-size`. Adjust the 0.8 multiplier in `updateGridSize()`.
- **Animation Speed**: Tweak CSS `animation: rain 1s` or adjust `drops[i] += 8` in `drawMatrix()`.
- **Fonts & Colors**: Modify CSS under `<style>` for branding or theme.

---

## Folder Structure

```
spot-the-mistake/
├── app.py              # Flask application
├── requirements.txt    # Python dependencies
├── README.md           # This file
└── LICENSE             # License details
```

---

## Contributing

1. Fork the repo.
2. Create a feature branch: `git checkout -b feature/YourFeature`
3. Commit your changes: `git commit -m "Add awesome feature"`
4. Push to branch: `git push origin feature/YourFeature`
5. Open a Pull Request.

---

## License

Apache License 2.0