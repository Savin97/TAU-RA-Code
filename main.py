#main.py
from pipeline.pipeline import run_pipeline

def main():
    print("--------------------\nStarting execution...\n--------------------")
    run_pipeline(system="martin")
    run_pipeline(system="uri")
    print("--------------------\nExecution Complete.")

if __name__ == "__main__":
    main()