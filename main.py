#main.py
from pipeline.pipeline import run_pipeline

def main():
    """
        system param for run_pipeline:
        Choose system = "martin" to include 0 root progressions.
        Choose system = "uri" to exclude them.
    """
    print("--------------------\nStarting execution...\n--------------------")
    run_pipeline(system="martin")
    print("--------------------\nExecution Complete.")

if __name__ == "__main__":
    main()