import time

if __name__ == "__main__":
    print("Starting Memory Stress Test...")
    dummy_data = []
    try:
        while True:
            # Append 10MB of data each iteration
            dummy_data.append(" " * 10 * 1024 * 1024)
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("Stopping Memory Stress Test...")
    except MemoryError:
        print("Memory exhausted.")
