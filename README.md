# Sales Data Management System

A comprehensive system for managing sales data, including database setup, data import/export, and API endpoints.

## Project Structure

```
.
├── app/                    # Main application directory
├── creation_data/         # Data files for initial setup
├── creation_scripts/      # Scripts for creating initial data
├── export_scripts/        # Scripts for exporting data
├── exports/              # Directory for exported data
├── import_scripts/       # Scripts for importing data
├── imports/             # Directory for imported data
├── migrations/          # Database migration files
└── various Python files for different functionalities
```

## Prerequisites

- Python 3.8 or higher
- SQLite3
- Virtual environment (recommended)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd <repository-name>
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Database Setup

The database setup process consists of two main steps:

1. **Create Database Schema**
   - This step creates the database structure with all necessary tables and relationships
   - Run the following command:
   ```bash
   python setup_database_schema.py
   ```

2. **Populate Database with Data**
   - This step imports data from CSV files into the database
   - Place your CSV data file named `sales-data-csv.txt` in the root directory
   - Run the following command:
   ```bash
   python setup_database.py
   ```

### Additional Database Management

- Apply migrations (if needed):
```bash
python apply_migrations.py
```

- Populate additional data (if needed):
```bash
python populate_empty_tables.py
```

## Usage

### Running the Application

Start the FastAPI server:
```bash
uvicorn main:app --reload
```

### Data Management

- Import data:
  - Place your data files in the `imports/` directory
  - Use the appropriate import script from `import_scripts/process_imports`

- Export data:
  - Use scripts from `export_scripts/` to export data
  - Exported files will be saved in the `exports/` directory

### Database Management

- Schema updates: Modify `schema.sql` and run migrations
- Data population: Use `populate_empty_tables.py` for initial data
- Database connection: Use `database.py` for database operations

## API Endpoints

The application provides various API endpoints for data management. Refer to the FastAPI documentation at `http://localhost:8000/docs` when the server is running.

## Dependencies

- FastAPI (v0.104.1)
- Uvicorn (v0.24.0)
- Python-Jose (v3.3.0)
- Python-Multipart (v0.0.6)
- Python-Dotenv (v1.0.0)
- OpenAI (v0.28.0)
- Streamlit (v1.32.0)
- HTTPX (v0.24.1)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

[Add your license information here]

## Support

[Add support information here] 