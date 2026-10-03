import time
import sys

def main():
    print("NovaBank Durability & A2A Worker started.")
    print("Connecting to Temporal server and waiting for events...")
    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        print("Worker stopped.")

if __name__ == "__main__":
    main()
