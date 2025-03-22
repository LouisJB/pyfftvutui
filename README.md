# pyfftvutui

A Python based TUI FFT and VU display.

This got started with an interactive session with ChatGPT
for a TUI (NCurses) FFT and VU.

My first AI coding experience.

Which I played with, extended and combined together.

Since it works well I thought worth keeping and perhaps explanding on
in the future.


Running
=======

you'll need Python 3 with numpy. I recommend using a Pythin venv for it

then once set up, run using

python3 fftui-no-norm-hz-labels.py

or

./run.sh


Installing venv
===============

notes on how to install the Python venv
from the project dir after checkout

python3 -m venv venv
source venv/bin/activate
python3 -m pip install numpy
python3 -m pip install pyaudio
python3 -m pip install curses
python3 -m pip install time
