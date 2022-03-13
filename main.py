# -*- coding: utf-8 -*-
import random

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtTest import *
from PyQt5.QtWidgets import *

import socket
import _thread
import argparse

argument_parser = argparse.ArgumentParser(description="Tic Tac Toe Game")
argument_parser.add_argument("--port", type=int, required=False, help="the port of the server", default=4095)
argument_parser.add_argument("--address", type=str, required=False, help="the address of the server", default="localhost")
try:
	arguments = argument_parser.parse_args()
	port = arguments.port
	address = arguments.address
except SystemExit:
	port = 4095
	address = "localhost"
	pass


class Square(QPushButton):
	def __init__(self, parent, x, y):
		super(Square, self).__init__(parent=parent)
		self.setCursor(Qt.CursorShape.PointingHandCursor)
		if x == y == 0:
			styles = " border-left: 1.5px solid black; border-top: 1.5px solid black;"
		elif x == 0 and y == 1:
			styles = " border-top: 1.5px solid black;"
		elif x == 0 and y == 2:
			styles = " border-right: 1.5px solid black; border-top: 1.5px solid black;"
		elif x == 1 and y == 0:
			styles = " border-left: 1.5px solid black;"
		elif x == 1 and y == 2:
			styles = " border-right: 1.5px solid black;"
		elif x == 2 and y == 0:
			styles = " border-left: 1.5px solid black; border-bottom: 1.5px solid black;"
		elif x == 2 and y == 1:
			styles = " border-bottom: 1.5px solid black;"
		elif x == y == 2:
			styles = " border-right: 1.5px solid black; border-bottom: 1.5px solid black;"
		else:
			styles = ""
		self.setStyleSheet("background-color: black; color: #888; font-size: 100px; border: 1.5px solid white;" + styles)
		self.setFixedSize(QSize(300, 300))
		self.move(QPoint(x * 300, y * 300))
		self.x_, self.y_ = x, y
		self.animation = self.animation_ = None
		self.position = ("a", "b", "c")[y] + str(3 - x)
		self.fixed = False
	
	def enterEvent(self, event):
		if not self.fixed:
			self.setText(self.parent().symbol)
			self.animation_ = QPropertyAnimation(self, b"color")
			self.animation_.setStartValue(QColor("black"))
			self.animation_.setEndValue(QColor("#888"))
			self.animation_.setDuration(350)
			self.animation_.start()
		self.animation = QPropertyAnimation(self, b"background")
		self.animation.setStartValue(QColor("black"))
		self.animation.setEndValue(QColor("#181818"))
		self.animation.setDuration(350)
		self.animation.start()
		super(Square, self).enterEvent(event)
	
	def leaveEvent(self, event) -> None:
		if not self.fixed:
			self.animation_ = QPropertyAnimation(self, b"color")
			self.animation_.setStartValue(QColor("#888"))
			self.animation_.setEndValue(QColor("black"))
			self.animation_.setDuration(350)
			self.animation_.finished.connect(lambda: self.setText(""))
			self.animation_.start()
		self.animation = QPropertyAnimation(self, b"background")
		self.animation.setStartValue(QColor("#181818"))
		self.animation.setEndValue(QColor("black"))
		self.animation.setDuration(350)
		self.animation.start()
		super(Square, self).leaveEvent(event)
	
	def mouseReleaseEvent(self, event) -> None:
		if self.fixed or self.parent().symbol != ("X", "0")[int(self.parent().parent().turn)] or not self.parent().parent().allow_moves:
			return
		if self.animation_ is not None:
			self.animation_.stop()
		self.parent().parent().socket.send(f"move {self.parent().parent().code} {self.position}".encode())
		self.fixed = self.parent().symbol
		self.setText(self.fixed)
		self.setStyleSheet(self.styleSheet().split("; ")[0] + f"; color: white; " + "; ".join(self.styleSheet().split("; ")[2:]))
		self.parent().parent().turn = not self.parent().parent().turn
		self.parent().parent().waiting_move_label.show()
		self.parent().parent().waiting_move_label.fadeIn()
		super(Square, self).mouseReleaseEvent(event)
	
	def setBackground(self, color):
		self.setStyleSheet(f"background-color: {color.name()}; " + "; ".join(self.styleSheet().split("; ")[1:]))
	
	def setColor(self, color):
		self.setStyleSheet(self.styleSheet().split("; ")[0] + f"; color: {color.name()}; " + "; ".join(self.styleSheet().split("; ")[2:]))
	
	background = pyqtProperty(QColor, fset=setBackground)
	color = pyqtProperty(QColor, fset=setColor)


class Board(QGroupBox):
	def __init__(self, parent):
		super(Board, self).__init__(parent=parent)
		self.setLayout(QGridLayout())
		self.squares = []
		self.setFixedSize(QSize(900, 900))
		for x in range(3):
			row = []
			for y in range(3):
				row.append(Square(self, x, y))
				self.layout().addWidget(row[-1], x, y)
			self.squares.append(row)
		self.symbol = "X"
		self.board = [[" ", " ", " "] for _ in range(3)]
	

class ActionButton(QPushButton):
	def __init__(self, parent, text="", font_size=25, background="white", hover_color="#C8C8C8"):
		super(ActionButton, self).__init__(text, parent)
		self.setStyleSheet(f"border: 10px solid {background}; background-color: {background};")
		self.animation = None
		self.setCursor(Qt.CursorShape.PointingHandCursor)
		self.setFont(QFont(QFontDatabase.applicationFontFamilies(QFontDatabase.addApplicationFont(QDir.currentPath() + "/fonts/Chakra_Petch/ChakraPetch-Medium.ttf"))[0], font_size))
		self.adjustSize()
		self.animating = False
		self.background_color = background
		self.hover_background_color = hover_color

	def enterEvent(self, event):
		if self.animating:
			return
		
		def removeAnimation():
			self.animation = None
		self.animation = QPropertyAnimation(self, b"background")
		self.animation.setStartValue(QColor(self.background_color))
		self.animation.setEndValue(QColor(self.hover_background_color))
		self.animation.setDuration(200)
		self.animation.finished.connect(removeAnimation)
		self.animation.start()
		super(ActionButton, self).enterEvent(event)
	
	def leaveEvent(self, event):
		if self.animating:
			return
		
		def removeAnimation():
			self.animation = None
		self.animation = QPropertyAnimation(self, b"background")
		self.animation.setStartValue(QColor(self.hover_background_color))
		self.animation.setEndValue(QColor(self.background_color))
		self.animation.setDuration(200)
		self.animation.finished.connect(removeAnimation)
		self.animation.start()
		super(ActionButton, self).leaveEvent(event)
	
	def setBackground(self, color):
		self.setStyleSheet(f"border: 10px solid {color.name()}; background-color: {color.name()};")
	
	background = pyqtProperty(QColor, fset=setBackground)


class LineEdit(QLineEdit):
	def __init__(self, parent):
		super(LineEdit, self).__init__(parent=parent)
		self.setAttribute(Qt.WidgetAttribute.WA_MacShowFocusRect, False)
		self.setStyleSheet("background-color: black; border: 5px solid black;")
		self.setFont(QFont(QFontDatabase.applicationFontFamilies(QFontDatabase.addApplicationFont(QDir.currentPath() + "/fonts/Nova_Mono/NovaMono-Regular.ttf"))[0], 20))
		self.setValidator(QIntValidator())
		self.animation = None
		self.setFixedWidth(160)
		self.setMaxLength(5)

	def fadeIn(self):
		self.animation = QPropertyAnimation(self, b"background")
		self.animation.setStartValue(QColor("black"))
		self.animation.setEndValue(QColor("white"))
		self.animation.setDuration(100)
		self.animation.start()
	
	def fadeOut(self):
		self.animation = QPropertyAnimation(self, b"background")
		self.animation.setStartValue(QColor("white"))
		self.animation.setEndValue(QColor("black"))
		self.animation.setDuration(100)
		self.animation.start()
	
	def setBackground(self, color):
		self.setStyleSheet(f"background-color: {color.name()}; border: 5px solid " + color.name())
	
	background = pyqtProperty(QColor, fset=setBackground)


class Label(QLabel):
	def __init__(self, parent, text="", font_size=20):
		super(Label, self).__init__(text, parent=parent)
		self.setStyleSheet("color: black;")
		self.setFont(QFont(QFontDatabase.applicationFontFamilies(QFontDatabase.addApplicationFont(QDir.currentPath() + "/fonts/Chakra_Petch/ChakraPetch-Light.ttf"))[0], font_size))
		self.setAlignment(Qt.AlignmentFlag.AlignHCenter)
		self.adjustSize()
		self.animation = None
		self.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
	
	def fadeIn(self):
		self.animation = QPropertyAnimation(self, b"color")
		self.animation.setStartValue(QColor("black"))
		self.animation.setEndValue(QColor("white"))
		self.animation.setDuration(100)
		self.animation.start()
	
	def fadeOut(self):
		self.animation = QPropertyAnimation(self, b"color")
		self.animation.setStartValue(QColor("white"))
		self.animation.setEndValue(QColor("black"))
		self.animation.setDuration(100)
		self.animation.start()
	
	def setColor(self, color):
		self.setStyleSheet("color: " + color.name())
	
	color = pyqtProperty(QColor, fset=setColor)
	

class Window(QMainWindow):
	def __init__(self):
		super(Window, self).__init__()
		self.setWindowTitle("Tic Tac Toe")
		self.setMinimumSize(QSize(1920, 1080))
		self.setStyleSheet("background-color: black;")
		self.title = QLabel("Tic Tac Toe", self)
		self.title.setFont(QFont(QFontDatabase.applicationFontFamilies(QFontDatabase.addApplicationFont(QDir.currentPath() + "/fonts/Bungee/Bungee-Regular.ttf"))[0], 100))
		self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
		self.title.setStyleSheet("color: white;")
		self.lesser_title = QLabel("But with sockets", self)
		self.lesser_title.setFont(QFont(QFontDatabase.applicationFontFamilies(QFontDatabase.addApplicationFont(QDir.currentPath() + "/fonts/Bungee_Hairline/BungeeHairline-Regular.ttf"))[0], 10))
		self.lesser_title.setStyleSheet("color: #888;")
		self.join_game = ActionButton(self, text="Join a game")
		self.join_game.pressed.connect(self.joinGame)
		self.create_game = ActionButton(self, text="Create a game")
		self.create_game.pressed.connect(self.createGame)
		self.game_id_label = Label(self, "Enter the game id")
		self.game_id_label.hide()
		self.game_id_input = LineEdit(self)
		self.game_id_input.hide()
		self.cancel_button = ActionButton(self, text="Cancel", font_size=12, background="#cd1e0b", hover_color="#eb3333")
		self.cancel_button.pressed.connect(self.cancelJoin)
		self.cancel_button.hide()
		self.join_button = ActionButton(self, text="Join Game", font_size=12, background="#009962", hover_color="#1eaf7a")
		self.join_button.pressed.connect(self.join)
		self.join_button.hide()
		self.join_error = Label(self, "An error occurred, try again later", 15)
		self.join_error.hide()
		self.cancel_create_button = ActionButton(self, text="Cancel", font_size=12, background="#cd1e0b", hover_color="#eb3333")
		self.cancel_create_button.pressed.connect(self.cancelCreate)
		self.cancel_create_button.hide()
		self.code_label = Label(self, "An error occurred, try again later")
		self.code_label.hide()
		self.waiting_label = Label(self, "Waiting for opponent...")
		self.waiting_label.hide()
		self.waiting_move_label = Label(self, "Waiting for opponent's move...")
		self.waiting_move_label.hide()
		self.board = Board(self)
		self.board.hide()
		self.join_game_animation = self.create_game_animation = None
		self.code = None
		self.creating = False
		self.allow_moves = True
		self.game_over_label = QLabel(self)
		self.game_over_label.setStyleSheet("color: white; background-color: rgba(255, 255, 255, 0.1); border: 75px solid transparent")
		self.game_over_label.setAlignment(Qt.AlignCenter)
		self.game_over_label.setFont(QFont(QFontDatabase.applicationFontFamilies(QFontDatabase.addApplicationFont(QDir.currentPath() + "/fonts/Chakra_Petch/ChakraPetch-Bold.ttf"))[0], 40))
		self.game_over_label.hide()
		self.socket = socket.socket()
		try:
			self.socket.connect((address, port))
		except ConnectionRefusedError:
			exit("Cannot connect to the server")
		except socket.gaierror:
			exit("Invalid hostname")
		except OverflowError:
			if port < 0:
				exit("Port number cannot be negative")
			exit("Port number too large or too small")
		except OSError:
			exit("Invalid port number")
		self.turn = None
		self.show()

	def listenMoves(self):
		while True:
			response = self.socket.recv(1024).decode()
			if response.strip() == "":
				break
			if response.startswith("result"):
				if not self.waiting_move_label.isHidden():
					self.waiting_move_label.hide()
				self.game_over_label.show()
				if not int(response.split()[1]):
					self.game_over_label.setText("Game Over! Tie Game")
				else:
					self.game_over_label.setText(f"Game Over! {('X', 'O')[int(response.split()[1]) - 1]} wins")
				self.game_over_label.adjustSize()
				self.game_over_label.move(QPoint((self.width() - self.game_over_label.width()) // 2, (self.height() - self.game_over_label.height()) // 2))
				self.allow_moves = False
				_thread.exit()
			self.turn = not self.turn
			self.waiting_move_label.hide()
			for x in self.board.squares:
				for y in x:
					if y.position == response.split()[2]:
						if y.animation_ is not None:
							y.animation_.stop()
						y.fixed = {"X": "0", "0": "X"}[self.board.symbol]
						y.setText(y.fixed)
						y.setStyleSheet(y.styleSheet().split("; ")[0] + f"; color: white; " + "; ".join(y.styleSheet().split("; ")[2:]))
						break
				else:
					continue
				break

	def join(self):
		if len(self.game_id_input.text()) != 5:
			self.join_error.show()
			self.join_error.setText(f"Game ID has a length of {len(self.game_id_input.text())}, expected 5")
			self.join_error.fadeIn()
			self.join_error.adjustSize()
			return
		self.socket.send(f"join {self.game_id_input.text()}".encode())
		response = self.socket.recv(1024)
		if not int(response):
			self.join_error.show()
			self.join_error.setText(f"Cannot find a game of id {self.game_id_input.text()}")
			self.join_error.fadeIn()
			self.join_error.adjustSize()
		elif int(response) == 2:
			self.join_error.show()
			self.join_error.setText(f"Game of id {self.game_id_input.text()} has already started")
			self.join_error.fadeIn()
			self.join_error.adjustSize()
		else:
			if not self.join_error.isHidden():
				self.join_error.fadeOut()
				self.join_error.hide()
			self.game_id_label.fadeOut()
			self.game_id_label.hide()
			self.game_id_input.fadeOut()
			self.game_id_input.hide()
			self.join_button.hide()
			self.cancel_button.hide()
			self.title.hide()
			self.lesser_title.hide()
			self.board.symbol = "0"
			self.board.show()
			self.code = self.game_id_input.text()
			_thread.start_new_thread(self.listenMoves, ())
			self.game_id_input.setText("")
			self.turn = False
			self.waiting_move_label.show()

	def cancelJoin(self):
		self.game_id_label.hide()
		self.game_id_label.fadeOut()
		self.game_id_input.hide()
		self.game_id_input.fadeOut()
		self.cancel_button.hide()
		self.join_button.hide()
		if not self.join_error.isHidden():
			self.join_error.fadeOut()
			self.join_error.hide()
		self.game_id_input.setText("")
		QTest.qWait(100)
		
		def removeJoinGameAnimation():
			self.join_game_animation = None
			self.join_game.animating = False
		
		def removeCreateGameAnimation():
			self.create_game_animation = None
			self.create_game.animating = False
		self.join_game.animating = True
		self.join_game.show()
		self.join_game_animation = QPropertyAnimation(self.join_game, b"background")
		self.join_game_animation.setStartValue(QColor("black"))
		self.join_game_animation.setEndValue(QColor("white"))
		self.join_game_animation.setDuration(100)
		self.join_game_animation.finished.connect(removeJoinGameAnimation)
		self.join_game_animation.start()
		self.create_game.animating = True
		self.create_game.show()
		self.create_game_animation = QPropertyAnimation(self.create_game, b"background")
		self.create_game_animation.setStartValue(QColor("black"))
		self.create_game_animation.setEndValue(QColor("white"))
		self.create_game_animation.setDuration(100)
		self.create_game_animation.finished.connect(removeCreateGameAnimation)
		self.create_game_animation.start()

	def cancelCreate(self):
		self.creating = False
		self.code_label.hide()
		self.code_label.fadeOut()
		self.waiting_label.hide()
		self.waiting_label.fadeOut()
		self.cancel_create_button.hide()
		self.join_button.hide()
		self.socket.send(f"cancel {self.code}".encode())
		QTest.qWait(100)
		
		def removeJoinGameAnimation():
			self.join_game_animation = None
			self.join_game.animating = False
		
		def removeCreateGameAnimation():
			self.create_game_animation = None
			self.create_game.animating = False
		self.join_game.animating = True
		self.join_game.show()
		self.join_game_animation = QPropertyAnimation(self.join_game, b"background")
		self.join_game_animation.setStartValue(QColor("black"))
		self.join_game_animation.setEndValue(QColor("white"))
		self.join_game_animation.setDuration(100)
		self.join_game_animation.finished.connect(removeJoinGameAnimation)
		self.join_game_animation.start()
		self.create_game.animating = True
		self.create_game.show()
		self.create_game_animation = QPropertyAnimation(self.create_game, b"background")
		self.create_game_animation.setStartValue(QColor("black"))
		self.create_game_animation.setEndValue(QColor("white"))
		self.create_game_animation.setDuration(100)
		self.create_game_animation.finished.connect(removeCreateGameAnimation)
		self.create_game_animation.start()

	def joinGame(self):
		def removeJoinGameAnimation():
			self.join_game_animation = None
			self.join_game.animating = False
			self.join_game.hide()
			self.game_id_label.show()
			self.game_id_label.fadeIn()
			self.game_id_input.show()
			self.game_id_input.fadeIn()
			self.cancel_button.show()
			self.join_button.show()
		
		def removeCreateGameAnimation():
			self.create_game_animation = None
			self.create_game.animating = False
			self.create_game.hide()
		self.join_game.animating = True
		self.join_game_animation = QPropertyAnimation(self.join_game, b"background")
		self.join_game_animation.setStartValue(QColor("#C8C8C8"))
		self.join_game_animation.setEndValue(QColor("black"))
		self.join_game_animation.setDuration(100)
		self.join_game_animation.finished.connect(removeJoinGameAnimation)
		self.join_game_animation.start()
		self.create_game.animating = True
		self.create_game_animation = QPropertyAnimation(self.create_game, b"background")
		self.create_game_animation.setStartValue(QColor("#C8C8C8"))
		self.create_game_animation.setEndValue(QColor("black"))
		self.create_game_animation.setDuration(100)
		self.create_game_animation.finished.connect(removeCreateGameAnimation)
		self.create_game_animation.start()

	def createGame(self):
		def removeJoinGameAnimation():
			self.join_game_animation = None
			self.join_game.animating = False
			self.join_game.hide()
			self.join_game.hide()
			self.code = str(random.randint(0, 99999)).zfill(5)
			self.code_label.show()
			self.code_label.setText("Code: " + self.code)
			self.code_label.fadeIn()
			self.waiting_label.show()
			self.waiting_label.fadeIn()
			self.cancel_create_button.show()
			self.creating = True
			self.socket.send(f"id {self.code}".encode())
			
			def checkForStart():
				while True:
					if not self.creating:
						break
					response = self.socket.recv(1024).decode()
					if response == "start":
						self.code_label.fadeOut()
						self.code_label.hide()
						self.waiting_label.fadeOut()
						self.waiting_label.hide()
						self.cancel_create_button.hide()
						self.title.hide()
						self.lesser_title.hide()
						self.board.symbol = "X"
						self.board.show()
						self.turn = False
						_thread.start_new_thread(self.listenMoves, ())
					break
				_thread.exit()
			_thread.start_new_thread(checkForStart, ())
		
		def removeCreateGameAnimation():
			self.create_game_animation = None
			self.create_game.animating = False
			self.create_game.hide()
		self.join_game.animating = True
		self.join_game_animation = QPropertyAnimation(self.join_game, b"background")
		self.join_game_animation.setStartValue(QColor("#C8C8C8"))
		self.join_game_animation.setEndValue(QColor("black"))
		self.join_game_animation.setDuration(100)
		self.join_game_animation.finished.connect(removeJoinGameAnimation)
		self.join_game_animation.start()
		self.create_game.animating = True
		self.create_game_animation = QPropertyAnimation(self.create_game, b"background")
		self.create_game_animation.setStartValue(QColor("#C8C8C8"))
		self.create_game_animation.setEndValue(QColor("black"))
		self.create_game_animation.setDuration(100)
		self.create_game_animation.finished.connect(removeCreateGameAnimation)
		self.create_game_animation.start()
	
	def resizeEvent(self, event):
		self.title.resize(QSize(event.size().width(), 100))
		self.lesser_title.move(QPoint((event.size().width() - self.lesser_title.width()) // 2, self.title.height()))
		self.join_game.move(QPoint((event.size().width() - self.join_game.width()) // 2, (event.size().height() // 2) - self.join_game.height() - 20))
		self.create_game.move(QPoint((event.size().width() - self.create_game.width()) // 2, (event.size().height() // 2) + 20))
		self.game_id_label.move(QPoint((event.size().width() - self.game_id_label.width()) // 2, (event.size().height() // 2) - self.game_id_label.height() - 10))
		self.game_id_input.move(QPoint((event.size().width() - self.game_id_input.width()) // 2, (event.size().height() // 2) + 10))
		self.cancel_button.move(QPoint(self.game_id_input.pos().x(), self.game_id_input.pos().y() + self.game_id_input.height() + 17))
		self.cancel_create_button.move(QPoint((event.size().width() - self.cancel_create_button.width()) // 2, self.game_id_input.pos().y() + self.game_id_input.height() + 17))
		self.join_button.move(QPoint(self.game_id_input.pos().x() + self.game_id_input.width() - self.join_button.width(), self.game_id_input.pos().y() + self.game_id_input.height() + 17))
		self.join_error.move(QPoint((event.size().width() - self.join_error.width()) // 2, self.cancel_button.pos().y() + self.cancel_button.height() + 17))
		self.code_label.move(QPoint((event.size().width() - self.code_label.width()) // 2, (event.size().height() // 2) - self.code_label.height() - 10))
		self.waiting_label.move(QPoint((event.size().width() - self.waiting_label.width()) // 2, (event.size().height() // 2) + 10))
		self.board.move(QPoint((event.size().width() - self.board.width()) // 2, (event.size().height() - self.board.height()) // 2))
		self.waiting_move_label.move(QPoint(self.board.x() + self.board.width() + 17, self.board.y()))
		self.game_over_label.move(QPoint((event.size().width() - self.game_over_label.width()) // 2, (event.size().height() - self.game_over_label.height()) // 2))
		super(Window, self).resizeEvent(event)


def stop():
	window.creating = False
	QTest.qWait(100)
	window.socket.send(b"end")


try:
	application, window = QApplication([]), Window()
	application.aboutToQuit.connect(stop)
	application.exec_()
except KeyboardInterrupt:
	exit(stop())
