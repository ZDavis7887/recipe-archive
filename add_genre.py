import sqlite3
import pandas as pd
import os

def build_db_from_csvs():
    db_name = "recipes.db"
    
    # Connect to SQLite (this creates the file if it doesn't exist)
    conn = sqlite3.connect(db_name)
    
    # Define your CSV files and their corresponding SQLite table names
    # Update these keys/values to match your actual file names!
    csv_mapping = {
        "allrecipes_az_massive_database.csv": "recipes",
      
    }

    for csv_file, table_name in csv_mapping.items():
        if os.path.exists(csv_file):
            print(f"Found {csv_file}. Reading headers and importing data into table '{table_name}'...")
            
            try:
                # Read the CSV file using pandas
                df = pd.read_csv(csv_file)
                
                # to_sql automatically creates the table using the exact CSV headers as column names!
                # if_exists='replace' means if you run this again, it safely refreshes the table.
                df.to_sql(table_name, conn, if_exists="replace", index=False)
                
                print(f"-> Successfully created table '{table_name}' with {len(df)} rows and columns: {list(df.columns)}\n")
                
            except Exception as e:
                print(f"Error processing {csv_file}: {e}\n")
        else:
            print(f"Skipping {csv_file}: File not found in this folder. (You can add it later!)\n")

    conn.close()
    print("Database build complete!")

if __name__ == "__main__":
    build_db_from_csvs()