#main.py
from pipeline.uri_pipeline import run_uri_pipeline

def main():
    print("\nStarting execution...\n--------------------")
    run_uri_pipeline()
    print("--------------------\nExecution Complete.")

if __name__ == "__main__":
    main()