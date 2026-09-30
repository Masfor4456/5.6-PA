"""
Name: Mason Ford
Date: 09/30/2026
Assignment: SQLite CRUD Python Application
Purpose: Create and manipulate the EN_ReviewData SQLite relational database
           using Python CRUD operations and data from the supplied JSON dataset.
"""

import json
import sqlite3
from pathlib import Path


DB_NAME = "EN_ReviewData.db"
DEFAULT_JSON_NAME = "dataset_en_dev.json"


# * Create/connect to the SQLite database and enforce foreign keys.
def connect_database():
    connection = sqlite3.connect(DB_NAME)
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


# * Read the supplied JSON/JSON-lines dataset.
def load_json_records(json_path):
    records = []

    with open(json_path, "r", encoding="utf-8") as json_file:
        # First try a normal JSON document.
        try:
            data = json.load(json_file)

            if isinstance(data, list):
                records = data
            elif isinstance(data, dict):
                records = [data]

        except json.JSONDecodeError:
            # The supplied class dataset may also be newline-delimited JSON.
            json_file.seek(0)

            for line_number, line in enumerate(json_file, start=1):
                line = line.strip()

                if not line:
                    continue

                try:
                    record = json.loads(line)
                    if isinstance(record, dict):
                        records.append(record)
                except json.JSONDecodeError as error:
                    print(f"Skipping invalid JSON on line {line_number}: {error}")

    return records


# * Create the relational tables and their primary/foreign keys.
def create_tables(connection):
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Categories (
            product_category TEXT PRIMARY KEY
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Reviewers (
            reviewer_id TEXT PRIMARY KEY
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Products (
            product_id TEXT PRIMARY KEY,
            product_category TEXT NOT NULL,
            FOREIGN KEY (product_category)
                REFERENCES Categories(product_category)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Reviews (
            review_id TEXT PRIMARY KEY,
            product_id TEXT NOT NULL,
            reviewer_id TEXT NOT NULL,
            stars INTEGER NOT NULL,
            review_body TEXT,
            review_title TEXT,
            FOREIGN KEY (product_id)
                REFERENCES Products(product_id),
            FOREIGN KEY (reviewer_id)
                REFERENCES Reviewers(reviewer_id)
        )
    """)

    connection.commit()


# * Insert the JSON dataset into the normalized relational tables.
def import_dataset(connection, json_path):
    records = load_json_records(json_path)

    if not records:
        print("No records were found in the JSON dataset.")
        return

    cursor = connection.cursor()

    categories = set()
    reviewers = set()
    products = {}

    reviews = []

    for record in records:
        review_id = record.get("review_id")
        product_id = record.get("product_id")
        reviewer_id = record.get("reviewer_id")
        stars = record.get("stars")
        review_body = record.get("review_body")
        review_title = record.get("review_title")
        product_category = record.get("product_category")

        if not all([
            review_id,
            product_id,
            reviewer_id,
            product_category
        ]):
            continue

        categories.add(product_category)
        reviewers.add(reviewer_id)

        # Keep one category for each product.
        # The dataset is expected to associate each product with one category.
        products[product_id] = product_category

        try:
            stars = int(stars)
        except (TypeError, ValueError):
            continue

        reviews.append((
            review_id,
            product_id,
            reviewer_id,
            stars,
            review_body,
            review_title
        ))

    cursor.executemany(
        "INSERT OR IGNORE INTO Categories (product_category) VALUES (?)",
        [(category,) for category in categories]
    )

    cursor.executemany(
        "INSERT OR IGNORE INTO Reviewers (reviewer_id) VALUES (?)",
        [(reviewer,) for reviewer in reviewers]
    )

    cursor.executemany(
        """
        INSERT OR IGNORE INTO Products
            (product_id, product_category)
        VALUES (?, ?)
        """,
        list(products.items())
    )

    cursor.executemany(
        """
        INSERT OR IGNORE INTO Reviews
            (review_id, product_id, reviewer_id, stars, review_body, review_title)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        reviews
    )

    connection.commit()

    print("\nDataset import completed.")
    print(f"Records read: {len(records)}")
    print(f"Categories inserted: {len(categories)}")
    print(f"Reviewers inserted: {len(reviewers)}")
    print(f"Products inserted: {len(products)}")
    print(f"Reviews inserted: {len(reviews)}")


# * Find the JSON dataset in the same folder as this Python program.
def get_dataset_path():
    script_folder = Path(__file__).resolve().parent
    default_path = script_folder / DEFAULT_JSON_NAME

    if default_path.exists():
        return default_path

    print("\nThe dataset was not found automatically.")
    print("Place the JSON file in the same folder as this Python file.")
    print("You can also enter the full path to the JSON file.")

    while True:
        entered_path = input("JSON dataset path: ").strip().strip('"')

        if not entered_path:
            print("Please enter a file path.")
            continue

        path = Path(entered_path)

        if path.exists() and path.is_file():
            return path

        print("That file was not found. Try again.")


# * Create a fresh database and import the dataset.
def initialize_database():
    if Path(DB_NAME).exists():
        print(f"\n{DB_NAME} already exists.")
        choice = input(
            "Delete it and create a fresh database? (Y/N): "
        ).strip().lower()

        if choice != "y":
            print("Database initialization cancelled.")
            return

        try:
            Path(DB_NAME).unlink()
            print("Existing database deleted.")
        except OSError as error:
            print(f"Could not delete the database: {error}")
            return

    json_path = get_dataset_path()

    connection = connect_database()

    try:
        create_tables(connection)
        import_dataset(connection, json_path)
    except sqlite3.Error as error:
        connection.rollback()
        print(f"Database error: {error}")
    finally:
        connection.close()


# * Display categories having at least a user-specified number of products.
def display_categories_by_product_count(connection):
    while True:
        try:
            minimum = int(
                input("Enter the minimum number of products: ").strip()
            )

            if minimum < 0:
                print("Enter zero or a positive number.")
                continue

            break

        except ValueError:
            print("Please enter a whole number.")

    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            c.product_category,
            COUNT(p.product_id) AS product_count
        FROM Categories c
        LEFT JOIN Products p
            ON c.product_category = p.product_category
        GROUP BY c.product_category
        HAVING COUNT(p.product_id) >= ?
        ORDER BY product_count DESC, c.product_category
    """, (minimum,))

    rows = cursor.fetchall()

    print("\nCategories meeting the requirement:")
    print("-" * 55)

    if not rows:
        print("No categories matched the requested minimum.")
        return

    for category, count in rows:
        print(f"{category:<35} {count:>8} products")


# * Allow the user to enter and execute a SELECT statement.
def execute_select(connection):
    print("\nEnter a SQL SELECT statement.")
    print("Example: SELECT * FROM Reviews LIMIT 10;")

    sql = input("SQL> ").strip()

    if not sql:
        print("No SQL statement entered.")
        return

    if not sql.upper().lstrip().startswith("SELECT"):
        print("Only SELECT statements are allowed in this option.")
        return

    cursor = connection.cursor()

    try:
        cursor.execute(sql)
        rows = cursor.fetchall()

        column_names = [description[0] for description in cursor.description]

        print("\nResults:")
        print("-" * 80)
        print(" | ".join(column_names))
        print("-" * 80)

        if not rows:
            print("No rows returned.")
            return

        for row in rows:
            print(" | ".join(str(value) for value in row))

        print(f"\nRows returned: {len(rows)}")

    except sqlite3.Error as error:
        print(f"SQL error: {error}")


# * Display table names and columns to help the user insert a row.
def show_table_columns(connection, table_name):
    cursor = connection.cursor()

    try:
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()

        if not columns:
            return []

        print(f"\n{table_name} columns:")
        for column in columns:
            print(f"- {column[1]} ({column[2]})")

        return columns

    except sqlite3.Error as error:
        print(f"Database error: {error}")
        return []


# * Insert a row into a user-selected table.
def insert_row(connection):
    tables = ["Categories", "Reviewers", "Products", "Reviews"]

    print("\nTables:")
    for index, table in enumerate(tables, start=1):
        print(f"{index}. {table}")

    choice = input("Select a table: ").strip()

    try:
        table_name = tables[int(choice) - 1]
    except (ValueError, IndexError):
        print("Invalid table selection.")
        return

    columns = show_table_columns(connection, table_name)

    if not columns:
        return

    values = []

    print("\nEnter a value for each column.")
    print("Press Enter to enter an empty value where allowed.")

    for column in columns:
        column_name = column[1]

        if column[5] == 1:
            print(f"{column_name} is a primary key.")

        value = input(f"{column_name}: ")

        if value == "":
            value = None

        if column[2].upper() == "INTEGER" and value is not None:
            try:
                value = int(value)
            except ValueError:
                print(f"{column_name} must be an integer.")
                return

        values.append(value)

    column_names = ", ".join(column[1] for column in columns)
    placeholders = ", ".join("?" for _ in columns)

    sql = f"""
        INSERT INTO {table_name} ({column_names})
        VALUES ({placeholders})
    """

    try:
        connection.execute(sql, values)
        connection.commit()
        print("Row inserted successfully.")

    except sqlite3.IntegrityError as error:
        connection.rollback()
        print(f"Insert failed: {error}")

    except sqlite3.Error as error:
        connection.rollback()
        print(f"Database error: {error}")


# * Update a row using its primary key to demonstrate the UPDATE operation.
def update_row(connection):
    tables = ["Categories", "Reviewers", "Products", "Reviews"]

    print("\nTables:")
    for index, table in enumerate(tables, start=1):
        print(f"{index}. {table}")

    choice = input("Select a table: ").strip()

    try:
        table_name = tables[int(choice) - 1]
    except (ValueError, IndexError):
        print("Invalid table selection.")
        return

    columns = show_table_columns(connection, table_name)

    if not columns:
        return

    primary_key = next((column[1] for column in columns if column[5] == 1), None)

    if primary_key is None:
        print("No primary key was found for this table.")
        return

    print(f"\nPrimary key: {primary_key}")
    key_value = input("Enter the primary-key value of the row to update: ").strip()

    matching_columns = [
        column[1]
        for column in columns
        if column[1] != primary_key
    ]

    print("\nColumns that can be updated:")
    for index, column_name in enumerate(matching_columns, start=1):
        print(f"{index}. {column_name}")

    column_choice = input("Select a column to update: ").strip()

    try:
        column_name = matching_columns[int(column_choice) - 1]
    except (ValueError, IndexError):
        print("Invalid column selection.")
        return

    new_value = input(f"Enter the new value for {column_name}: ")

    selected_column = next(
        column for column in columns if column[1] == column_name
    )

    if selected_column[2].upper() == "INTEGER":
        try:
            new_value = int(new_value)
        except ValueError:
            print(f"{column_name} must be an integer.")
            return

    sql = f"""
        UPDATE {table_name}
        SET {column_name} = ?
        WHERE {primary_key} = ?
    """

    try:
        cursor = connection.execute(sql, (new_value, key_value))
        connection.commit()

        if cursor.rowcount == 0:
            print("No matching row was found.")
        else:
            print("Row updated successfully.")

    except sqlite3.IntegrityError as error:
        connection.rollback()
        print(f"Update failed: {error}")

    except sqlite3.Error as error:
        connection.rollback()
        print(f"Database error: {error}")


# * Delete all Reviews records for a user-entered product category.
def delete_reviews_by_category(connection):
    category = input(
        "Enter the product category whose reviews should be deleted: "
    ).strip()

    if not category:
        print("A category is required.")
        return

    cursor = connection.cursor()

    try:
        cursor.execute("""
            DELETE FROM Reviews
            WHERE product_id IN (
                SELECT product_id
                FROM Products
                WHERE product_category = ?
            )
        """, (category,))

        connection.commit()

        print(
            f"{cursor.rowcount} review(s) deleted for category '{category}'."
        )

    except sqlite3.Error as error:
        connection.rollback()
        print(f"Delete failed: {error}")


# * Delete all database tables as required by the assignment.
def delete_all_tables(connection):
    print("\nWARNING: This will permanently delete all four tables and their data.")

    confirmation = input(
        "Type DELETE to continue: "
    ).strip()

    if confirmation != "DELETE":
        print("Operation cancelled.")
        return False

    cursor = connection.cursor()

    # Child tables must be removed before parent tables because of foreign keys.
    tables = ["Reviews", "Products", "Reviewers", "Categories"]

    try:
        for table in tables:
            cursor.execute(f"DROP TABLE IF EXISTS {table}")

        connection.commit()
        print("All database tables have been deleted.")
        return True

    except sqlite3.Error as error:
        connection.rollback()
        print(f"Could not delete all tables: {error}")
        return False


# * Display the main menu and allow the user to select database operations.
def display_menu():
    print("\n" + "=" * 65)
    print("             EN_ReviewData SQLite Application")
    print("=" * 65)
    print("1. Create/recreate database and import JSON dataset")
    print("2. Display categories with at least N products")
    print("3. Execute a SQL SELECT statement")
    print("4. Insert a row into a table")
    print("5. Update a row in a table")
    print("6. Delete Reviews by product category")
    print("7. Delete all tables")
    print("8. Exit")
    print("=" * 65)


# * Run the application menu and connect all required functions.
def main():
    print("=" * 65)
    print("EN_ReviewData SQLite CRUD Application")
    print("=" * 65)

    connection = None

    while True:
        display_menu()
        choice = input("Select an option: ").strip()

        if choice == "1":
            initialize_database()

            # Reconnect after initialization because the previous connection
            # was intentionally closed by initialize_database().
            if connection is not None:
                connection.close()

            if Path(DB_NAME).exists():
                connection = connect_database()

        elif choice in {"2", "3", "4", "5", "6", "7"}:
            if connection is None:
                if not Path(DB_NAME).exists():
                    print("\nThe database does not exist yet.")
                    print("Select option 1 first.")
                    continue

                connection = connect_database()

            try:
                if choice == "2":
                    display_categories_by_product_count(connection)

                elif choice == "3":
                    execute_select(connection)

                elif choice == "4":
                    insert_row(connection)

                elif choice == "5":
                    update_row(connection)

                elif choice == "6":
                    delete_reviews_by_category(connection)

                elif choice == "7":
                    deleted = delete_all_tables(connection)

                    if deleted:
                        connection.close()
                        connection = None

            except sqlite3.Error as error:
                print(f"Database error: {error}")

        elif choice == "8":
            if connection is not None:
                connection.close()

            print("Program ended.")
            break

        else:
            print("Invalid selection. Please choose an option from 1 to 8.")


if __name__ == "__main__":
    main()
