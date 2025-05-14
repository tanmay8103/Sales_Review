import sqlite3
import pandas as pd
import re
import os
import datetime
import csv

# --- Configuration ---
DATABASE_FILE = 'sales_data.db'
# Ensure this filename matches the actual CSV file you are using
CSV_FILE = 'sales-data-csv.txt'

# --- Helper Functions ---

def clean_amount(amount_str):
    if not amount_str:
        return None
    # Remove 'USD ' prefix and any commas
    amount_str = amount_str.replace('USD ', '').replace(',', '')
    try:
        return float(amount_str)
    except ValueError:
        return None

def parse_date(date_str):
    if not date_str:
        return None
    try:
        # Try different date formats
        for fmt in ['%m/%d/%Y', '%Y-%m-%d']:
            try:
                return datetime.strptime(date_str, fmt).strftime('%Y-%m-%d')
            except ValueError:
                continue
        return None
    except Exception:
        return None

def clean_percentage(pct_str):
    if not pct_str:
        return None
    try:
        return int(pct_str.strip('%'))
    except ValueError:
        return None

def clean_stage_name(stage_str):
    """Extracts the descriptive part of the stage string."""
    if pd.isna(stage_str) or not isinstance(stage_str, str) or stage_str.strip() == "":
        return "Unknown" # Default stage if missing/invalid
    # Example: "5 - Commitment to Buy - Commit" -> "Commitment to Buy - Commit"
    parts = stage_str.split(' - ', 1)
    if len(parts) > 1:
        if parts[0].isdigit():
            return parts[1].strip()
        else:
             return stage_str.strip()
    return stage_str.strip() # Return original if format is unexpected

def get_or_create_record(cursor, table_name, name_column, name_value, other_columns=None):
    """Gets the ID of a record by name, or creates it if it doesn't exist."""
    if pd.isna(name_value) or (isinstance(name_value, str) and name_value.strip() == ""):
        print(f"Warning: Cannot get/create record in {table_name} with empty/null name value.")
        return None

    name_value_str = str(name_value).strip()
    if not name_value_str:
         print(f"Warning: Cannot get/create record in {table_name} with empty/null name value after stripping.")
         return None

    # Using LOWER() for case-insensitive lookup
    cursor.execute(f"SELECT {table_name[:-1]}_id FROM {table_name} WHERE LOWER({name_column}) = LOWER(?)", (name_value_str,))
    result = cursor.fetchone()

    if result:
        return result[0]
    else:
        # Create new record
        cols_to_insert = [name_column]
        vals_to_insert = [name_value_str] # Use the original stripped value for insertion
        placeholders = ["?"]

        if other_columns:
            for col, val in other_columns.items():
                if pd.isna(val):
                    val = None
                elif isinstance(val, str):
                    val = val.strip()
                elif isinstance(val, (int, float)):
                     if pd.api.types.is_integer_dtype(type(val)) and not isinstance(val, int):
                         val = int(val)
                     elif pd.api.types.is_float_dtype(type(val)) and not isinstance(val, float):
                         val = float(val)
                cols_to_insert.append(col)
                vals_to_insert.append(val)
                placeholders.append("?")

        sql = f"INSERT INTO {table_name} ({', '.join(cols_to_insert)}) VALUES ({', '.join(placeholders)})"
        try:
            cursor.execute(sql, tuple(vals_to_insert))
            print(f"Inserted into {table_name}: {name_column}={name_value_str}")
            return cursor.lastrowid
        except sqlite3.IntegrityError as e:
            print(f"IntegrityError inserting into {table_name} for '{name_value_str}': {e}. Attempting lookup again.")
            cursor.execute(f"SELECT {table_name[:-1]}_id FROM {table_name} WHERE LOWER({name_column}) = LOWER(?)", (name_value_str,))
            result = cursor.fetchone()
            if result:
                return result[0]
            else:
                print(f"Error: Failed to insert or find record in {table_name} for '{name_value_str}' after IntegrityError.")
                return None
        except Exception as e:
            print(f"Error inserting into {table_name} ({name_column}='{name_value_str}'): {e}")
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
        # First read the CSV using Python's csv module to handle quoting properly
        print(f"Reading CSV file: {csv_file} with csv module...")
        rows = []
        with open(csv_file, 'r', newline='') as f:
            reader = csv.reader(f, quoting=csv.QUOTE_MINIMAL)
            header = next(reader)  # Get header row
            for row in reader:
                if len(row) > 0 and not row[0].strip().startswith('Subtotal'):
                    rows.append(row)
        
        # Convert to pandas DataFrame
        df = pd.DataFrame(rows, columns=header)
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
        df['Probability_Percentage_Clean'] = df['Probability_Percentage'].apply(clean_percentage)
        df['Age_Clean'] = pd.to_numeric(df['Age'], errors='coerce').astype('Int64') # Convert Age to nullable Int64

        # Filter out subtotal rows if they exist (check common patterns)
        initial_rows = len(df)
        df = df[~df['Fiscal_Period'].str.contains("Subtotal", na=False, case=False)] # Case-insensitive check
        filtered_rows = len(df)
        if initial_rows > filtered_rows:
             print(f"Filtered out {initial_rows - filtered_rows} 'Subtotal' rows.")
        print(f"Processing {filtered_rows} data rows after filtering.")

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
        print("\n--- Processing Rows ---")
        for index, row in df.iterrows():

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
                if owner_name:
                    first_name = owner_name.split(' ')[0]
                    last_name = ' '.join(owner_name.split(' ')[1:]) if len(owner_name.split(' ')) > 1 else 'Unknown'
                    username = (first_name[0] + last_name).lower().replace(" ", "").replace(".", "") if first_name and last_name != 'Unknown' else owner_name.lower().replace(" ", "").replace(".", "")
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
                'opportunity_owner': row['Opportunity_Owner'],
                'stage_name': row['Stage'],
                'next_step': row['Next_Step'],
                'close_date': row['Close_Date_Clean'],
                'total_amount': row['Total_Opportunity_Amount_Clean'],
                'currency': 'USD' if pd.notna(row['Total_Opportunity_Amount_Clean']) else None,
                'probability_percentage': row['Probability_Percentage_Clean'],
                'age': row['Age_Clean'],
                'created_date': row['Created_Date_Clean'],
                'fiscal_period': row['Fiscal_Period'],
                'lead_source': row['Lead_Source'],
                'type': row['Type'],
                'is_closed': 0,
                'is_won': 0
            }

            if pd.isna(opportunity_data['created_date']):
                 print(f"Warning: Row {index+1} ({row['Opportunity_Name']}) missing Created_Date. Using today's date.")
                 opportunity_data['created_date'] = datetime.date.today().strftime('%Y-%m-%d')

            # 5. Insert Opportunity
            cols = ', '.join(opportunity_data.keys())
            placeholders = ', '.join('?' * len(opportunity_data))
            sql = f"INSERT OR IGNORE INTO opportunities ({cols}) VALUES ({placeholders})"

            values_tuple = tuple(
                item.item() if isinstance(item, pd.NA.__class__) else # Convert pd.NA to None
                int(item) if pd.api.types.is_integer_dtype(type(item)) and pd.notna(item) and not isinstance(item, int) else
                float(item) if pd.api.types.is_float_dtype(type(item)) and pd.notna(item) and not isinstance(item, float) else
                str(item).strip() if isinstance(item, str) else # Strip string values before insert
                item
                for item in opportunity_data.values()
            )

            try:
                cursor.execute(sql, values_tuple)
                if cursor.rowcount > 0:
                    inserted_count += 1
            except sqlite3.IntegrityError as ie:
                 print(f"IntegrityError inserting opportunity '{row['Opportunity_Name']}': {ie}")
                 print(f"Data: {opportunity_data}")
                 print(f"Tuple: {values_tuple}")
                 skipped_count += 1
            except Exception as e:
                 print(f"Error inserting opportunity '{row['Opportunity_Name']}': {e}")
                 print(f"Data: {opportunity_data}")
                 print(f"Tuple: {values_tuple}")
                 skipped_count += 1

        conn.commit()
        print(f"\n--- Population Summary ---")
        print(f"Processed {filtered_rows} data rows.")
        print(f"Inserted {inserted_count} opportunities.")
        print(f"Skipped {skipped_count} rows (due to errors, missing essential data, or duplicates).")
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
    # Make sure the script is being run with the correct filename
    # If the script is named database.py, this call is correct
    populate_database(DATABASE_FILE, CSV_FILE)
    # If the script is named populate_db.py, it should be run as such