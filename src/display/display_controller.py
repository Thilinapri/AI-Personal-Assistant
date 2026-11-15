
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

except ImportError:
    from display_manager import draw_screen as draw_home_screen
    from screen_reminders import draw_reminder_screen
    from screen_memories import draw_memory_screen


# ==========================================
# EchoMind Display Configuration
# ==========================================

WIDTH = 320
HEIGHT = 240

DC_PIN = 25
RST_PIN = 24

BACKGROUND = (10, 17, 32)

SPI_SPEED = 4000000

HOME_DURATION = 8
REMINDER_DURATION = 5
MEMORY_DURATION = 5

DATA_REFRESH_INTERVAL = 5

SCREENS = [
    ("home", HOME_DURATION),
    ("reminder", REMINDER_DURATION),
    ("memory", MEMORY_DURATION),
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

        self.last_data_refresh = 0

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

                self.latest_reminder = {
                    "reminder_time": reminder[2],
                    "title": reminder[6],
                    "content": reminder[7],
                }

            else:

                self.latest_reminder = None

            # ----------------------------------
            # Latest saved memory
            # ----------------------------------

            memories = self.database.get_all_memories()

            if memories:

                memory = memories[0]

                self.latest_memory = {
                    "category": memory[1],
                    "title": memory[2],
                    "content": memory[3],
                    "date": memory[4],
                    "time": memory[5],
                    "notification": memory[6],
                    "created_at": memory[7],
                }

            else:

                self.latest_memory = None

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

        return display

    # ======================================
    # Main Display Loop
    # ======================================

    def run(self):

        display = None

        try:

            print("Starting EchoMind Display Worker...")

            display = self.initialize_display()

            screen_index = 0
            screen_started = time.monotonic()

            frame = 0
            last_render = 0

            print("Automatic screen rotation started.")

            while not self.stop_event.is_set():

                now = time.monotonic()

                # ----------------------------------
                # Refresh database periodically
                # ----------------------------------

                if (
                    self.database is not None
                    and now - self.last_data_refresh >= self.refresh_interval
                ):

                    self.refresh_database_data()

                # ----------------------------------
                # Screen rotation
                # ----------------------------------

                screen_name, duration = SCREENS[screen_index]

                if now - screen_started >= duration:

                    screen_index = (
                        screen_index + 1
                    ) % len(SCREENS)

                    screen_started = now
                    frame = 0
                    last_render = 0

                    screen_name, duration = SCREENS[screen_index]

                    print("Display changing screen:", screen_name)

                    continue

                # ----------------------------------
                # Home screen
                # ----------------------------------

                if screen_name == "home":

                    draw_home_screen(display, frame)

                    frame += 1

                    self.stop_event.wait(0.12)

                # ----------------------------------
                # Upcoming reminder screen
                # ----------------------------------

                elif screen_name == "reminder":

                    if now - last_render >= 1:

                        if self.database is None:

                            # Standalone demo mode
                            draw_reminder_screen(display)

                        else:

                            # Live database mode
                            draw_reminder_screen(
                                display,
                                reminder=self.latest_reminder,
                                live_data=True
                            )

                        last_render = now

                    self.stop_event.wait(0.05)

                # ----------------------------------
                # Recently added memory screen
                # ----------------------------------

                elif screen_name == "memory":

                    if now - last_render >= 1:

                        if self.database is None:

                            # Standalone demo mode
                            draw_memory_screen(display)

                        else:

                            # Live database mode
                            draw_memory_screen(
                                display,
                                memory=self.latest_memory,
                                live_data=True
                            )

                        last_render = now

                    self.stop_event.wait(0.05)

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


# ==========================================
# Standalone Display Test
# ==========================================

def main():

    worker = DisplayWorker(database=None)

    try:

        worker.start()

        print("Standalone display test started.")
        print("Press CTRL+C to stop.")

        while worker.is_alive():
            worker.join(timeout=1)

    except KeyboardInterrupt:

        print("\nStopping standalone display test...")

        worker.stop()
        worker.join()

    print("Standalone display test finished.")


if __name__ == "__main__":
    main()
