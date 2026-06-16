#main.py
from pipeline.pipeline import run_pipeline

N = [1,2]
def main():
    """
        system param for run_pipeline:
        Choose system = "final" to include 0 root progressions.
        Choose system = "uri" to exclude them.
    """
    print("--------------------\nStarting execution...\n--------------------")
    for n in N:
        print(f"--------------------\nn={n}\n--------------------")
        run_pipeline(system="final", n = n)
    print("--------------------\nExecution Complete.")

if __name__ == "__main__":
    main()