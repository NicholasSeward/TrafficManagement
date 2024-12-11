import subprocess
from concurrent.futures import ThreadPoolExecutor

def run_car():
    try:
        result = subprocess.run(['python', 'car.py'], capture_output=True, text=True)
        print(result.stdout)
        print(result.stderr, end='')
    except Exception as e:
        print(f"Error running car.py: {e}")

def main():
    # Number of parallel executions
    num_processes = 10
    
    with ThreadPoolExecutor(max_workers=num_processes) as executor:
        futures = [executor.submit(run_car) for _ in range(num_processes)]
        for future in futures:
            try:
                future.result()  # To catch exceptions if any
            except Exception as e:
                print(f"Execution failed: {e}")

if __name__ == "__main__":
    main()
