import sqlite3
import pandas as pd
import re
import os
import datetime

# --- Configuration ---
DATABASE_FILE = 'sales_data.db'
CSV_FILE = 'sales-data-csv.txt' # The name of your uploaded CSV file

# --- Helper Functions ---

def clean_amount(amount_str):
    """Removes currency symbols, commas, and converts to float."""
    if pd.isna(amount_str) or not isinstance(amount_str, str) or amount_str.strip() == "":
        return None
    # Remove 'USD ' prefix and commas
    cleaned = re.sub(r'[^\d.]', '', amount_str.replace('USD', '').strip())
    try:
        return float(cleaned)
    except ValueError:
        print(f"Warning: Could not convert amount '{amount_str}' to float. Returning None.")
        return None

def parse_date(date_str):
    """Converts various date formats (e.g., MM/DD/YYYY) to YYYY-MM-DD string."""
    if pd.isna(date_str) or not isinstance(date_str, str) or date_str.strip() == "":
        return None
    try:
        # Attempt to parse standard formats like MM/DD/YYYY
        dt_obj = datetime.datetime.strptime(date_str.strip(), '%m/%d/%Y')
        return dt_obj.strftime('%Y-%m-%d')
    except ValueError:
        print(f"Warning: Could not parse date '{date_str}'. Returning None.")
        return None # Handle other formats or errors as needed

def clean_stage_name(stage_str):
    """Extracts the descriptive part of the stage string."""
    if pd.isna(stage_str) or not isinstance(stage_str, str) or stage_str.strip() == "":
        return "Unknown" # Default stage if missing/invalid
    # Example: "5 - Commitment to Buy - Commit" -> "Commitment to Buy - Commit"
    parts = stage_str.split(' - ', 1)
    if len(parts) > 1:
        return parts[1].strip()
    return stage_str.strip() # Return original if format is unexpected

def get_or_create_record(cursor, table_name, name_column, name_value, other_columns=None):
    """Gets the ID of a record by name, or creates it if it doesn't exist."""
    if pd.isna(name_value) or (isinstance(name_value, str) and name_value.strip() == ""):
        return None # Cannot get/create record with no name

    # Ensure name_value is treated as a string for lookup/insert
    name_value_str = str(name_value).strip()
    if not name_value_str:
         return None

    # Try to find existing record
    cursor.execute(f"SELECT {table_name[:-1]}_id FROM {table_name} WHERE {name_column} = ?", (name_value_str,))
    result = cursor.fetchone()

    if result:
        return result[0]
    else:
        # Create new record
        cols_to_insert = [name_column]
        vals_to_insert = [name_value_str]
        placeholders = ["?"]

        if other_columns:
            for col, val in other_columns.items():
                 # Handle potential NaN values from pandas before inserting
                if pd.isna(val):
                    val = None
                elif isinstance(val, (int, float)):
                     # Check for pandas integer types that might cause issues
                     if pd.api.types.is_integer_dtype(type(val)) and not isinstance(val, int):
                         val = int(val) # Convert pandas integer types to standard python int
                     elif pd.api.types.is_float_dtype(type(val)) and not isinstance(val, float):
                         val = float(val) # Convert pandas float types to standard python float
                cols_to_insert.append(col)
                vals_to_insert.append(val)
                placeholders.append("?")

        sql = f"INSERT INTO {table_name} ({', '.join(cols_to_insert)}) VALUES ({', '.join(placeholders)})"
        try:
            cursor.execute(sql, tuple(vals_to_insert))
            print(f"Inserted into {table_name}: {name_column}={name_value_str}")
            return cursor.lastrowid
        except sqlite3.IntegrityError as e:
             # Handle potential race conditions or unique constraint violations gracefully
            print(f"IntegrityError inserting into {table_name} for {name_value_str}: {e}. Attempting lookup again.")
            cursor.execute(f"SELECT {table_name[:-1]}_id FROM {table_name} WHERE {name_column} = ?", (name_value_str,))
            result = cursor.fetchone()
            if result:
                return result[0]
            else:
                print(f"Error: Failed to insert or find record in {table_name} for {name_value_str} after IntegrityError.")
                return None # Failed to insert or find
        except Exception as e:
            print(f"Error inserting into {table_name} ({name_column}={name_value_str}): {e}")
            print(f"SQL: {sql}")
            print(f"Values: {tuple(vals_to_insert)}")
            return None


# --- Main Population Function ---

def populate_database(db_file, csv_file):
    """Reads the CSV and populates the SQLite database."""
    if not os.path.exists(csv_file):
        print(f"Error: CSV file not found at '{csv_file}'")
        return
    if not os.path.exists(db_file):
        print(f"Error: Database file not found at '{db_file}'. Please run the schema creation script first.")
        return

    conn = None
    try:
        # Use pandas to read CSV - handles potential quoting/comma issues better
        # Specify dtype=str to prevent pandas from auto-interpreting types initially
        df = pd.read_csv(csv_file, dtype=str, keep_default_na=False) # Keep empty strings as is initially
        print(f"Read {len(df)} rows from {csv_file}")

        # Replace empty strings with None for easier handling later
        df.replace("", None, inplace=True)

        # --- Data Cleaning ---
        print("Cleaning data...")
        df['Total_Opportunity_Amount_Clean'] = df['Total_Opportunity_Amount'].apply(clean_amount)
        df['Close_Date_Clean'] = df['Close_Date'].apply(parse_date)
        df['Created_Date_Clean'] = df['Created_Date'].apply(parse_date)
        df['Stage_Clean'] = df['Stage'].apply(clean_stage_name)
        # Clean Probability - remove '%' and convert to integer
        df['Probability_Percentage_Clean'] = df['Probability_Percentage'].str.replace('%', '', regex=False).astype(float).astype('Int64') # Use nullable Int64
        df['Age_Clean'] = pd.to_numeric(df['Age'], errors='coerce').astype('Int64') # Convert Age to nullable Int64

        # Filter out subtotal rows if they exist (check common patterns)
        df = df[~df['Fiscal_Period'].str.contains("Subtotal", na=False)]
        print(f"Processing {len(df)} data rows after filtering.")

        # --- Database Operations ---
        print(f"Connecting to database: {db_file}")
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        print("Connection successful.")

        # Enable Foreign Key support
        cursor.execute("PRAGMA foreign_keys = ON;")
        print("Foreign key support enabled.")

        # --- Process and Insert Data ---
        inserted_count = 0
        skipped_count = 0
        for index, row in df.iterrows():
            print(f"\nProcessing row {index+1}...")

            # 1. Get or Create Account
            account_name = row['Account_Name']
            account_id = get_or_create_record(cursor, 'accounts', 'account_name', account_name)
            if account_id is None:
                print(f"Skipping row {index+1}: Could not get or create Account '{account_name}'")
                skipped_count += 1
                continue

            # 2. Get or Create User (Opportunity Owner)
            owner_name = row['Opportunity_Owner']
            user_id = None
            if pd.notna(owner_name):
                owner_name = owner_name.strip()
                first_name = owner_name.split(' ')[0]
                last_name = ' '.join(owner_name.split(' ')[1:]) if len(owner_name.split(' ')) > 1 else 'Unknown'
                # Create a simple username (e.g., first initial + last name lowercased)
                username = (first_name[0] + last_name).lower().replace(" ", "") if first_name and last_name != 'Unknown' else owner_name.lower().replace(" ", "")
                user_id = get_or_create_record(cursor, 'users', 'username', username,
                                               other_columns={'first_name': first_name, 'last_name': last_name, 'full_name': owner_name})
            if user_id is None:
                 print(f"Skipping row {index+1}: Could not get or create User '{owner_name}'")
                 skipped_count += 1
                 continue

            # 3. Get or Create Stage
            stage_name_clean = row['Stage_Clean']
            stage_id = get_or_create_record(cursor, 'stages', 'stage_name', stage_name_clean)
            if stage_id is None:
                print(f"Skipping row {index+1}: Could not get or create Stage '{stage_name_clean}'")
                skipped_count += 1
                continue

            # 4. Prepare Opportunity Data
            opportunity_data = {
                'opportunity_name': row['Opportunity_Name'],
                'account_id': account_id,
                'owner_id': user_id,
                'stage_id': stage_id,
                'opportunity_owner': row['Opportunity_Owner'], # Keep original CSV value
                'stage_name': row['Stage'],                 # Keep original CSV value
                'next_step': row['Next_Step'],
                'close_date': row['Close_Date_Clean'],
                'total_amount': row['Total_Opportunity_Amount_Clean'],
                'currency': 'USD' if pd.notna(row['Total_Opportunity_Amount_Clean']) else None, # Assume USD if amount exists
                'probability_percentage': row['Probability_Percentage_Clean'],
                'age': row['Age_Clean'],
                'created_date': row['Created_Date_Clean'],
                # 'last_modified_date': Handled by trigger/default in DB
                'fiscal_period': row['Fiscal_Period'],
                'lead_source': row['Lead_Source'],
                'type': row['Type'],
                # is_closed / is_won might need logic based on Stage, default is False
                'is_closed': 0, # Default to False (0)
                'is_won': 0     # Default to False (0)
            }

            # Handle missing created_date (set a default if necessary, though schema requires it)
            if pd.isna(opportunity_data['created_date']):
                 print(f"Warning: Row {index+1} missing Created_Date. Using today's date.")
                 opportunity_data['created_date'] = datetime.date.today().strftime('%Y-%m-%d')


            # 5. Insert Opportunity (using INSERT OR IGNORE to avoid duplicates if script is run multiple times)
            # More robust would be to check existence first based on a unique combination if one exists
            cols = ', '.join(opportunity_data.keys())
            placeholders = ', '.join('?' * len(opportunity_data))
            sql = f"INSERT OR IGNORE INTO opportunities ({cols}) VALUES ({placeholders})"

            try:
                cursor.execute(sql, tuple(opportunity_data.values()))
                if cursor.rowcount > 0:
                    inserted_count += 1
                    print(f"Inserted Opportunity: {row['Opportunity_Name']}")
                else:
                    print(f"Skipped inserting potentially duplicate Opportunity: {row['Opportunity_Name']}")
                    skipped_count += 1
            except Exception as e:
                 print(f"Error inserting opportunity '{row['Opportunity_Name']}': {e}")
                 print(f"Data: {opportunity_data}")
                 skipped_count += 1


        # Commit changes
        conn.commit()
        print(f"\n--- Population Summary ---")
        print(f"Processed {len(df)} data rows.")
        print(f"Inserted {inserted_count} opportunities.")
        print(f"Skipped {skipped_count} rows (due to errors or duplicates).")
        print("✅ Database population complete.")

    except pd.errors.EmptyDataError:
        print(f"Error: CSV file '{csv_file}' is empty or invalid.")
    except Exception as e:
        print(f"❌ An error occurred during database population: {e}")
        if conn:
            conn.rollback()
            print("Changes rolled back.")
    finally:
        if conn:
            conn.close()
            print("Database connection closed.")


# --- Main Execution ---
if __name__ == "__main__":
    populate_database(DATABASE_FILE, CSV_FILE)