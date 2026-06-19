import time
import urllib.request
import threading

def network_hog():
    while True:
        try:
            # Make a fast, repetitive request
            urllib.request.urlopen("http://google.com")
        except Exception:
            pass

if __name__ == "__main__":
    print("Starting Network Stress Test...")
    threads = []
    for _ in range(50):
        t = threading.Thread(target=network_hog)
        t.daemon = True
        t.start()
        threads.append(t)
    
    try:
        time.sleep(30)
    except KeyboardInterrupt:
        pass
    finally:
        print("Stopping Network Stress Test...")
