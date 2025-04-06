import argparse
import curses
import os

import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import html2text



class EpubReader:
	def __init__(self, stdscr, epub_path):
		self.stdscr = stdscr
		self.epub_path = epub_path
		self.book = epub.read_epub(epub_path)
		self.items = [item for item in self.book.get_items() if item.get_type() == ebooklib.ITEM_DOCUMENT]
		self.current_page = 0
		self.html_parser = html2text.HTML2Text()
		self.html_parser.ignore_links = True
		self.html_parser.ignore_images = True
		self.max_y, self.max_x = self.stdscr.getmaxyx()
		self.lines_per_page = self.max_y - 4  # Leave space for UI and padding
		self.cols_per_page = (self.max_x // 2) - 6  # Two pages side by side with padding
		self.pages = self.process_pages()
		self.run()

	def process_pages(self):
		pages = []
		for item in self.items:
			soup = BeautifulSoup(item.content, 'html.parser')
			text = self.html_parser.handle(str(soup))
			lines = text.split('\n')
			chunk = []
			buffer = ""
			for line in lines:
				line = line.strip()
				if not line:  # Blank line before paragraphs
					if buffer:
						chunk.append(buffer)
						chunk.append("")  # Extra blank line
						buffer = ""
					continue
				words = line.split()
				for word in words:
					if len(buffer) + len(word) + 1 > self.cols_per_page:
						chunk.append(buffer)
						buffer = word
					else:
						buffer += (" " if buffer else "") + word
			if buffer:
				chunk.append(buffer)

			while chunk:
				pages.append(chunk[:self.lines_per_page])
				chunk = chunk[self.lines_per_page:]

			# Add an empty page after each chapter
			pages.append([" " * self.cols_per_page for _ in range(self.lines_per_page)])
		return pages

	def draw(self):
		self.stdscr.clear()
		left_page = self.pages[self.current_page] if self.current_page < len(self.pages) else []
		right_page = self.pages[self.current_page + 1] if self.current_page + 1 < len(self.pages) else []
		for i, line in enumerate(left_page):
			self.stdscr.addstr(i + 2, 3, line[:self.cols_per_page])
		for i, line in enumerate(right_page):
			self.stdscr.addstr(i + 2, self.cols_per_page + 9, line[:self.cols_per_page])
		self.stdscr.refresh()

	def run(self):
		while True:
			self.draw()
			key = self.stdscr.getch()
			if key == ord('q'):
				break
			elif key == curses.KEY_RIGHT:
				self.current_page = min(self.current_page + 2, len(self.pages) - 1)
			elif key == curses.KEY_LEFT:
				self.current_page = max(self.current_page - 2, 0)
			elif key == curses.KEY_END:
				self.current_page = len(self.pages) - 1
			elif key == curses.KEY_HOME:
				self.current_page = 0


def read_epub(stdscr, epub_path):
	curses.curs_set(0)
	stdscr.keypad(True)
	reader = EpubReader(stdscr, epub_path)


def main():
	parser = argparse.ArgumentParser(description="epubread.py - Reading EPUB files in the terminal.")

	# Positional argument: Path
	parser.add_argument("path", type=str, help="Path to the EPUB file")
	args = parser.parse_args()
	if not args.path.endswith('.epub'):
		print(f"Files format NOT supported: '{args.path}'"); return
	elif not os.path.isfile(args.path):
		print(f"File NOT found: '{args.path}'"); return

	epub_path = args.path
	curses.wrapper(read_epub, epub_path)


if __name__ == "__main__":
	main()
