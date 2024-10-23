# Slither24

*!!!Developing!!! Please report bugs*

## Intro

**Slither24** is a multiplayer snake-like game built using **Python** and **pygame**. Players connect to a server, control their snake, and compete with other players in real-time. The game is designed to be lightweight and supports both server and client components, allowing players to host their own game servers.

## How to Play

1. Set up your server.
2. Run the client to join the game.
3. Control your snake to grow in size, avoid collisions, and outmaneuver opponents.

## Installation

1.	Clone the repository:

```
git clone https://github.com/neilc24/slither24.git

cd slither24
```

2.	Install dependencies:

- You will need Python 3.x and pygame. Install the required Python modules:
```
pip install pygame
```

## Running the Game

1. To host a game, run the server:
```
python server.py
```

The server will start listening for client connections.

2. Once the server is up, players can join by running the client:
```
python client.py
```

The client will connect to the server and start the game.

3. To run the game locally (for debugging and demonstration):
```
python local_play.py
```

## Game Controls

- Move snake: Use the mouse to control the direction of the snake.

- Speed up: Hold the spacebar to move faster.

## Game Configuration

You can customize the game by editing the `config.py` file.

*Notice: When deployed on a cloud server, change the `HOST` variable to your server's public ip.*

## Contact

Author: Neil (Github:@neilc24)