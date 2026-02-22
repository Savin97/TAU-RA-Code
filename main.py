#main.py
from pipeline.pipeline import run_pipeline

def main():
    print("\nStarting execution...\n--------------------")
    run_pipeline(system="uri")
    run_pipeline(system="martin")
    print("--------------------\nExecution Complete.")

if __name__ == "__main__":
    main()