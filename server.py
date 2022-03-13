# -*- coding: utf-8 -*-
try:
	print("\033[38;5;39mStarting TCP server...\033[38;5;51m\nImporting modules...\033[0m ")
	import time
	start_ = time.time()
	print("\t\033[38;5;46mImported\033[38;5;105m time")
	start = time.time()
	import socket as socket_module
	print("\t\033[38;5;46mImported\033[38;5;105m socket")
	import argparse
	print("\t\033[38;5;46mImported\033[38;5;105m argparse")
	import _thread
	print("\t\033[38;5;46mImported\033[38;5;105m thread")
	import random
	print("\t\033[38;5;46mImported\033[38;5;105m random")
	print(f"\033[38;5;51mModule imports\033[38;5;48m complete\033[38;5;51m, took \033[38;5;57m{(time.time() - start):.20f}s\n\033[38;5;51mParsing arguments...", end="")
	start = time.time()
	argument_parser = argparse.ArgumentParser(description="Server script")
	argument_parser.add_argument("--port", type=int, required=False, help="the port to host the server on", default=4095)
	try:
		arguments = argument_parser.parse_args()
		port = arguments.port
	except SystemExit:
		port = 4095
		pass
	print(f" \033[38;5;48m complete\033[38;5;51m, took \033[38;5;57m{(time.time() - start):.20f}s\n\033[38;5;51mCreating socket... |", end="\r")
	start = time.time()
	socket = socket_module.socket()
	for i in range(1, random.randint(2, 7) + 1):
		time.sleep(0.15)
		print(f"Creating socket... " + ("|", "/", "—", "\\")[i % 4], end="\r")
	if port < 1024:
		print(f"Creating socket... \033[38;5;48m complete\033[38;5;51m, took \033[38;5;57m{(time.time() - start):.20f}s\n\033[93mWARNING: The given port number ({port}) is less than 1024 and cannot be bound, defaulting to port 4095.\n\033[38;5;51mBinding socket to port 4095...", end="\r")
		port = 4095
	elif port > 65535:
		print(f"Creating socket... \033[38;5;48m complete\033[38;5;51m, took \033[38;5;57m{(time.time() - start):.20f}s\n\033[93mWARNING: The given port number ({port}) is larger than 65535 and cannot be bound, defaulting to port 4095.\n\033[38;5;51mBinding socket to port 4095...", end="\r")
		port = 4095
	else:
		print(f"Creating socket... \033[38;5;48m complete\033[38;5;51m, took \033[38;5;57m{(time.time() - start):.20f}s\n\033[38;5;51mBinding socket to port {port}... |", end="\r")
	start = time.time()
	socket.bind(("", port))
	for i in range(1, random.randint(2, 7) + 1):
		time.sleep(0.15)
		print(f"Binding socket to port {port}... " + ("|", "/", "—", "\\")[i % 4], end="\r")
	print(f"Binding socket to port {port}... \033[38;5;48m complete\033[38;5;51m, took \033[38;5;57m{(time.time() - start):.20f}s\n\033[38;5;51mPreparing to listen on port... |", end="\r")
	start = time.time()
	socket.listen(5)
	for i in range(1, random.randint(10, 20) + 1):
		time.sleep(0.15)
		print("Preparing to listen on port... " + ("|", "/", "—", "\\")[i % 4], end="\r")
	print(f"Preparing to listen on port... \033[38;5;48m complete\033[38;5;51m, took \033[38;5;57m{(time.time() - start):.20f}s\n\033[38;5;51mSuccessfully started listening on port {port}, initialization took \033[38;5;57m{(time.time() - start_):.25f}s\033[0m\n")
	games = {}

	def listenInput():
		while True:
			data = input()
			try:
				if data.startswith("turn "):
					print(games[data.split()[1]]["turn"])
				elif data.startswith("board "):
					print(games[data.split()[1]]["board"][0])
					print(games[data.split()[1]]["board"][1])
					print(games[data.split()[1]]["board"][2])
				else:
					print(f"\033[91mInvalid command: '{data}'\033[0m")
			except:
				print(f"\033[91mInvalid command parameters: '{' '.join(data.split(' ')[1:])}'\033[0m")
		
	_thread.start_new_thread(listenInput, ())

	def game_over(board):
		"""
		Returns a tuple of two values
		[0] (tie_game): Whether the game is tied
		[1] (winner): The player who won the game, or None if the game is a tie
		If the game is not over, returns False, None
		"""
		# diagonal win
		if board[0][0] == board[1][1] == board[2][2] and board[0][0] != 0:
			return False, board[0][0]
		elif board[0][2] == board[1][1] == board[2][0] and board[0][2] != 0:
			return False, board[0][2]
		# horizontal win
		for i in range(3):
			if board[i][0] == board[i][1] == board[i][2] and board[i][0] != 0:
				return False, board[i][0]
		# vertical win
		for i in range(3):
			if board[0][i] == board[1][i] == board[2][i] and board[0][i] != 0:
				return False, board[0][i]

		# Check for tie game
		for r in range(3):
			for c in range(3):
				if board[r][c] == 0:
					return False, None
		
		return True, None

	def newConnection(connection_, address_):
		while True:
			response = connection_.recv(1024).decode()
			if response.startswith("id "):
				games[response.split()[1]] = {"status": "waiting", "moves": [], "connection": connection_, "turn": True}
			elif response.startswith("join "):
				for i in games.keys():
					if i == response.split()[1]:
						if games[i]["status"] == "started":
							connection_.send(b"2")
						else:
							games[i]["status"] = "started"
							games[i]["connection2"] = connection_
							connection_.send(b"1")
							games[i]["connection"].send(b"start")
							games[i]["board"] = [[0, 0, 0] for _ in range(3)]
						break
				else:
					connection_.send(b"0")
			elif response.startswith("cancel "):
				del games[response.split()[1]]
			elif response.startswith("move "):
				games[response.split()[1]]["moves"].append(response.split()[2])
				games[response.split()[1]]["turn"] = not games[response.split()[1]]["turn"]
				if connection_ == games[response.split()[1]]["connection"]:
					games[response.split()[1]]["connection2"].send(response.encode())
				else:
					games[response.split()[1]]["connection"].send(response.encode())
				games[response.split()[1]]["board"][3 - int(response.split()[2][1])][["a", "b", "c"].index(response.split()[2][0])] = int(games[response.split()[1]]["turn"]) + 1
				result = game_over(games[response.split()[1]]["board"])
				if result[0]:
					games[response.split()[1]]["connection2"].send(b"result 0")
					games[response.split()[1]]["connection"].send(b"result 0")
				elif result[1] is not None:
					games[response.split()[1]]["connection2"].send(("result " + str(result[1])).encode())
					games[response.split()[1]]["connection"].send(("result " + str(result[1])).encode())
			elif response.startswith("turn "):
				connection_.send(bytes(games[response.split()[1]]["turn"]))
			elif response.startswith("board "):
				connection_.send(bytes(games[response.split()[1]]["board"][0]))
				connection_.send(bytes(games[response.split()[1]]["board"][1]))
				connection_.send(bytes(games[response.split()[1]]["board"][2]))
			elif response == "end":
				print(f"\033[38;5;48mConnection from {address_[0]}:{address_[1]} closed by client\033[0m")
				break
			else:
				print(f"\033[38;5;48mConnection from {address_[0]}:{address_[1]} closed due to invalid command: '{response}'\033[0m")
				break
			print(f"\033[38;5;57m{address_[0]}:{address_[1]}: {response}\033[0m")
		connection_.close()

	while True:
		connection, address = socket.accept()
		print(f"\033[38;5;48mReceived connection from {address[0]} at port {address[1]}\033[0m")
		_thread.start_new_thread(newConnection, (connection, address))
except KeyboardInterrupt:
	print("\033[0m")
	exit()
