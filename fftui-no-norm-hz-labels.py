import pyaudio
import numpy as np
import curses
import time

# Audio Configuration
CHUNK = 1024  # Number of audio samples per frame
RATE = 44100  # Audio sampling rate

# Initialize audio stream
p = pyaudio.PyAudio()
stream = p.open(
    format=pyaudio.paInt16,
    channels=1,
    rate=RATE,
    input=True,
    frames_per_buffer=CHUNK
)

MODE_FFT = 0
MODE_WAVEFORM = 1
MODE_BOTH = 2
PEAK_DECAY = 0.05
VU_PEAK_DECAY = 0.4

peak_values = np.zeros(CHUNK // 2 + 1)

max_db = 0
min_db = -60

rms_left = 0
peak_rms_left = -60
no_of_colour_bands = 15

NOISE_FLOOR = 1e-4

def calculate_db(samples):
    rms = np.sqrt(np.mean(np.square(samples.astype(np.double))))
    if rms < NOISE_FLOOR:
        return -60.0  # Return minimum dB for silence
    db = 20 * np.log10(rms / 32768 + 1e-10)
    return max(db, -60.0)

def draw_fft(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(1)

    # Initialize colors
    curses.start_color()
    for i in range(1, 16):
        curses.init_pair(i, i, curses.COLOR_BLACK)

    mode = MODE_FFT

    while True:
        # Read audio data
        try:
            data = np.frombuffer(stream.read(CHUNK, exception_on_overflow=False), dtype=np.int16)
        except IOError:
            continue

        stdscr.clear()
        width = curses.COLS
        height = curses.LINES - 2
        fft_width = width - 9

        stdscr.addstr(0, width // 2 - 10, f"FFT/VU v0.1")

        if mode == MODE_FFT or mode == MODE_BOTH:
            # Perform FFT
            fft_data = np.abs(np.fft.rfft(data))
            freqs = np.fft.rfftfreq(CHUNK, 1/RATE)

            # Apply logarithmic scaling to frequency bins
            log_freqs = np.log10(1 + freqs)
            log_fft = fft_data * log_freqs

            # Smooth peak hold
            global peak_values
            peak_values = np.maximum(peak_values * (1 - PEAK_DECAY), log_fft)

            # Draw FFT bars
            for i in range(min(len(log_fft), fft_width)):
                bar_height = int(log_fft[i] / 65535)
                bar_height = min(bar_height, height)
                color_level = min(no_of_colour_bands - int((bar_height / height) * no_of_colour_bands), no_of_colour_bands)

                # Draw bar
                for j in range(bar_height):
                    try:
                        stdscr.addch(height-j, i, "#", curses.color_pair(color_level))
                    except curses.error:
                        pass

                # Draw peak hold
                peak_height = int(peak_values[i] / 65535)
                peak_height = min(peak_height, height)
                try:
                    stdscr.addch(height-peak_height, i, "'", curses.color_pair(7))
                except curses.error:
                    pass

            # Draw frequency labels
            for i in range(0, fft_width, fft_width // 10):
                freq = int(freqs[int(i * len(freqs) / fft_width)])
                stdscr.addstr(height + 1, i, f"{freq}Hz")

            # Draw RMS meters

            # Calculate RMS dB
            global rms_left
            old_rms_left = rms_left
            inst_rms_left = calculate_db(data)
            rms_left = (inst_rms_left + old_rms_left) / 2.0
            # rms_right = calculate_db(data_right)
            stdscr.addstr(0, 0, f"{rms_left:.2f}dB RMS")

            global peak_rms_left, peak_rms_right
            peak_rms_left = max(peak_rms_left - VU_PEAK_DECAY, inst_rms_left)
            # peak_rms_right = max(peak_rms_right - PEAK_DECAY, rms_right)

            # draw channel VU meter
            firstPeak = True
            for i in range(height):
                db_level = min_db + (i / height) * (max_db - min_db)
                color = min(no_of_colour_bands - int((db_level - min_db) / (max_db - min_db) * no_of_colour_bands), no_of_colour_bands)
                stdscr.addstr(height-i-1, width - 9, f"{db_level:.1f}dB", curses.color_pair(color))
                
                if (firstPeak == True) and (peak_rms_left <= db_level):
                    stdscr.addch(height-i-1, width-1, '_', curses.color_pair(color))
                    firstPeak = False

                if rms_left >= db_level:
                    #color = min(no_of_colour_bands - int((rms_left - min_db) / (max_db - min_db) * no_of_colour_bands), no_of_colour_bands)
                    stdscr.addch(height-i-1, width-1, '#', curses.color_pair(color))

        if mode == MODE_WAVEFORM or mode == MODE_BOTH:
            # Draw raw waveform
            for i in range(min(len(data), fft_width)):
                y = int((((int(data[i])) + 32768) / 65536) * height)
                color_level = min(int((y / height) * 7) + 1, 7)
                try:
                    stdscr.addch(height-y, i, "*", curses.color_pair(color_level))
                except curses.error:
                    pass

        stdscr.refresh()
        time.sleep(0.05)

        # Handle keypress
        key = stdscr.getch()
        if key == ord('q'):
            break
        elif key == ord('w'):
            # Toggle between FFT and Waveform
            mode = MODE_WAVEFORM if mode == MODE_FFT else MODE_FFT
        
        elif key == ord('b'):
            # Toggle between FFT and Both modes
            mode = MODE_BOTH if mode == MODE_FFT else MODE_FFT

# Run the TUI visualizer
curses.wrapper(draw_fft)

# Close the stream
stream.stop_stream()
stream.close()
p.terminate()
