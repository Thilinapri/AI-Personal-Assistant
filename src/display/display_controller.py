import time
import threading

import RPi.GPIO as GPIO
import st7789
from PIL import Image

# ==========================================
# Screen imports
# Support both package and standalone modes
# ==========================================

try:
    from .display_manager import draw_screen as draw_home_screen
    from .screen_reminders import draw_reminder_screen
    from .screen_memories import draw_memory_screen
    from .screen_notifications import draw_notification_screen
    from .screen_transcript import draw_transcript_screen

except ImportError:
    from display_manager import draw_screen as draw_home_screen
    from screen_reminders import draw_reminder_screen
    from screen_memories import draw_memory_screen
    from screen_notifications import draw_notification_screen
    from screen_transcript import draw_transcript_screen


# ==========================================
# EchoMind Display Configuration
# ==========================================

WIDTH = 320
HEIGHT = 240

DC_PIN = 25
RST_PIN = 24

BACKGROUND = (10, 17, 32)

SPI_SPEED = 4000000

DATA_REFRESH_INTERVAL = 5

PREVIOUS_BUTTON_PIN = 5
LISTENING_BUTTON_PIN = 6
NEXT_BUTTON_PIN = 13

BUTTON_POLL_DELAY = 0.03
BUTTON_DEBOUNCE_DELAY = 0.25

SCREENS = [
    "home",
    "reminder",
    "memory",
    "notifications",
    "transcript",
]


# ==========================================
# Display Worker
# Runs alongside the main EchoMind app
# ==========================================

class DisplayWorker(threading.Thread):

    def __init__(
        self,
        database=None,
        refresh_interval=DATA_REFRESH_INTERVAL
    ):

        super().__init__(
            daemon=True,
            name="EchoMindDisplayWorker"
        )

        self.database = database
        self.refresh_interval = refresh_interval

        self.stop_event = threading.Event()

        self.latest_reminder = None
        self.latest_memory = None
        self.latest_transcript = "No transcript yet"

        self.listening_enabled = True

        self.last_data_refresh = 0

        self.current_screen_index = 0

        self.previous_button_state = GPIO.HIGH
        self.listening_button_state = GPIO.HIGH
        self.next_button_state = GPIO.HIGH

        self.previous_button_time = 0
        self.listening_button_time = 0
        self.next_button_time = 0

        self.data_changed = True
        self.transcript_changed = True

        self.data_lock = threading.Lock()

    # ======================================
    # Store latest completed transcription
    # ======================================

    def update_transcript(self, transcription):
        """Store the latest completed transcription."""

        with self.data_lock:
            self.latest_transcript = transcription
            self.transcript_changed = True

    # ======================================
    # Fetch live database information
    # ======================================

    def refresh_database_data(self):

        if self.database is None:
            return

        try:

            # ----------------------------------
            # Upcoming reminder
            # ----------------------------------

            reminders = self.database.get_all_reminders()

            pending_reminders = [
                reminder
                for reminder in reminders
                if str(reminder[3]).lower() == "pending"
            ]

            if pending_reminders:

                reminder = pending_reminders[0]

                latest_reminder = {
                    "reminder_time": reminder[2],
                    "title": reminder[6],
                    "content": reminder[7],
                }

            else:

                latest_reminder = None

            # ----------------------------------
            # Latest saved memory
            # ----------------------------------

            memories = self.database.get_all_memories()

            if memories:

                memory = memories[0]

                latest_memory = {
                    "category": memory[1],
                    "title": memory[2],
                    "content": memory[3],
                    "date": memory[4],
                    "time": memory[5],
                    "notification": memory[6],
                    "created_at": memory[7],
                }

            else:

                latest_memory = None

            latest_listening_enabled = (
                self.database.get_listening_enabled()
            )

            with self.data_lock:

                data_changed = (
                    latest_reminder != self.latest_reminder
                    or latest_memory != self.latest_memory
                    or latest_listening_enabled != self.listening_enabled
                )

                self.latest_reminder = latest_reminder
                self.latest_memory = latest_memory
                self.listening_enabled = latest_listening_enabled

                if data_changed:
                    self.data_changed = True

            self.last_data_refresh = time.monotonic()

            print("Display: Database data refreshed.")

        except Exception as error:

            print(
                "Display: Database refresh failed:",
                repr(error)
            )

    # ======================================
    # Initialize TFT
    # ======================================

    def initialize_display(self):

        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)

        GPIO.setup(
            PREVIOUS_BUTTON_PIN,
            GPIO.IN,
            pull_up_down=GPIO.PUD_UP
        )

        GPIO.setup(
            LISTENING_BUTTON_PIN,
            GPIO.IN,
            pull_up_down=GPIO.PUD_UP
        )

        GPIO.setup(
            NEXT_BUTTON_PIN,
            GPIO.IN,
            pull_up_down=GPIO.PUD_UP
        )

        display = st7789.ST7789(
            port=0,
            cs=0,
            dc=DC_PIN,
            rst=RST_PIN,
            backlight=None,
            width=WIDTH,
            height=HEIGHT,
            rotation=0,
            invert=True,
            spi_speed_hz=SPI_SPEED,
            offset_left=0,
            offset_top=0
        )

        display.reset()
        time.sleep(0.2)
        display._init()

        print("EchoMind TFT initialized successfully.")
        print("Display buttons initialized:")
        print("  GPIO 5  - Previous screen")
        print("  GPIO 6  - Toggle listening")
        print("  GPIO 13 - Next screen")

        return display

    # ======================================
    # Button Handling
    # ======================================

    def setup_button_states(self):

        self.previous_button_state = GPIO.input(PREVIOUS_BUTTON_PIN)
        self.listening_button_state = GPIO.input(LISTENING_BUTTON_PIN)
        self.next_button_state = GPIO.input(NEXT_BUTTON_PIN)

        self.previous_button_time = time.monotonic()
        self.listening_button_time = time.monotonic()
        self.next_button_time = time.monotonic()

    def handle_buttons(self):

        now = time.monotonic()

        previous_state = GPIO.input(PREVIOUS_BUTTON_PIN)

        if (
            previous_state == GPIO.LOW
            and self.previous_button_state == GPIO.HIGH
            and now - self.previous_button_time >= BUTTON_DEBOUNCE_DELAY
        ):
            self.previous_button_time = now
            self.change_screen(-1)

        self.previous_button_state = previous_state

        listening_state = GPIO.input(LISTENING_BUTTON_PIN)

        if (
            listening_state == GPIO.LOW
            and self.listening_button_state == GPIO.HIGH
            and now - self.listening_button_time >= BUTTON_DEBOUNCE_DELAY
        ):
            self.listening_button_time = now
            self.toggle_listening()

        self.listening_button_state = listening_state

        next_state = GPIO.input(NEXT_BUTTON_PIN)

        if (
            next_state == GPIO.LOW
            and self.next_button_state == GPIO.HIGH
            and now - self.next_button_time >= BUTTON_DEBOUNCE_DELAY
        ):
            self.next_button_time = now
            self.change_screen(1)

        self.next_button_state = next_state

    def change_screen(self, direction):

        self.current_screen_index = (
            self.current_screen_index + direction
        ) % len(SCREENS)

        print(
            "Display screen changed:",
            SCREENS[self.current_screen_index]
        )

    def toggle_listening(self):

        if self.database is None:
            print("Display: Listening toggle unavailable without database.")
            return

        try:

            enabled = not self.database.get_listening_enabled()

            self.database.set_listening_enabled(enabled)

            with self.data_lock:
                self.listening_enabled = enabled
                self.data_changed = True

            if enabled:
                print("Display: Listening enabled.")
            else:
                print("Display: Listening paused.")

        except Exception as error:

            print(
                "Display: Listening toggle failed:",
                repr(error)
            )

    # ======================================
    # Main Display Loop
    # ======================================

    def run(self):

        display = None

        try:

            print("Starting EchoMind Display Worker...")

            display = self.initialize_display()

            self.setup_button_states()

            frame = 0
            last_render = 0

            while not self.stop_event.is_set():

                now = time.monotonic()

                self.handle_buttons()

                if (
                    self.database is not None
                    and now - self.last_data_refresh >= self.refresh_interval
                ):
                    self.refresh_database_data()

                screen_name = SCREENS[self.current_screen_index]

                if screen_name == "home":

                    should_render = False

                    with self.data_lock:
                        listening_enabled = self.listening_enabled

                        if self.data_changed:
                            should_render = True
                            self.data_changed = False

                    if (
                        now - last_render >= 0.12
                        or should_render
                    ):

                        draw_home_screen(
                            display,
                            frame,
                            listening_enabled
                        )

                        frame += 1
                        last_render = now

                    self.stop_event.wait(0.03)

                else:

                    should_render = False

                    with self.data_lock:
                        if self.data_changed:
                            should_render = True
                            self.data_changed = False

                        if self.transcript_changed:
                            should_render = True
                            self.transcript_changed = False

                    if now - last_render >= 1 or should_render:

                        if screen_name == "reminder":

                            if self.database is None:
                                draw_reminder_screen(display)
                            else:
                                with self.data_lock:
                                    reminder = self.latest_reminder

                                draw_reminder_screen(
                                    display,
                                    reminder=reminder,
                                    live_data=True
                                )

                        elif screen_name == "memory":

                            if self.database is None:
                                draw_memory_screen(display)
                            else:
                                with self.data_lock:
                                    memory = self.latest_memory

                                draw_memory_screen(
                                    display,
                                    memory=memory,
                                    live_data=True
                                )

                        elif screen_name == "notifications":

                            with self.data_lock:
                                reminder = self.latest_reminder

                            draw_notification_screen(
                                display,
                                frame,
                                reminder=reminder
                            )

                        elif screen_name == "transcript":

                            with self.data_lock:
                                transcription = self.latest_transcript
                                listening_enabled = self.listening_enabled

                            draw_transcript_screen(
                                display,
                                transcription,
                                listening_enabled
                            )

                        last_render = now

                    self.stop_event.wait(0.03)

        except Exception as error:

            print(
                "Display worker error:",
                repr(error)
            )

        finally:

            if display is not None:

                try:

                    display.display(
                        Image.new(
                            "RGB",
                            (WIDTH, HEIGHT),
                            BACKGROUND
                        )
                    )

                except Exception:
                    pass

            GPIO.cleanup()

            print("EchoMind Display Worker stopped.")
            print("GPIO cleanup complete.")

    # ======================================
    # Stop Worker
    # ======================================

    def stop(self):

        self.stop_event.set()