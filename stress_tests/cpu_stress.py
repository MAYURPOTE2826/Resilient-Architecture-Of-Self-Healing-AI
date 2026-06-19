import multiprocessing
import time

def cpu_hog():
    while True:
        pass

if __name__ == "__main__":
    print("Starting CPU Stress Test...")
    processes = []
    # Use multiple cores to spike overall CPU usage
    for _ in range(multiprocessing.cpu_count()):
        p = multiprocessing.Process(target=cpu_hog)
        p.start()
        processes.append(p)
    
    try:
        time.sleep(30) # Run for 30 seconds
    except KeyboardInterrupt:
        pass
    finally:
        print("Stopping CPU Stress Test...")
        for p in processes:
            p.terminate()
