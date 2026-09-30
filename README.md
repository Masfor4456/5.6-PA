# EN ReviewData SQLite Application

A Python application that creates and manages a SQLite database using review data from a supplied JSON dataset.

## Project Overview

This project demonstrates how Python can be used with SQLite to create a relational database and perform CRUD (Create, Read, Update, Delete) operations.

The application uses the `sqlite3` library included with Python and imports data from the `dataset_en_dev.json` file.

## Database Structure

The application creates a database named:

`EN_ReviewData.db`

The database contains four tables:

- **Reviewers**
  - `reviewer_id` — Primary Key

- **Categories**
  - `product_category` — Primary Key

- **Products**
  - `product_id` — Primary Key
  - `product_category` — Foreign Key to `Categories`

- **Reviews**
  - `review_id` — Primary Key
  - `product_id` — Foreign Key to `Products`
  - `reviewer_id` — Foreign Key to `Reviewers`
  - `stars`
  - `review_body`
  - `review_title`

## Features

The application provides a menu with the following options:

1. Create or recreate the database and import the JSON dataset
2. Display categories with at least a user-specified number of products
3. Execute SQL `SELECT` statements
4. Insert a row into a table
5. Update a row in a table
6. Delete reviews by product category
7. Delete all tables
8. Exit the application

## Requirements

- Python 3
- SQLite3
- `dataset_en_dev.json`

The `sqlite3` library is included with Python, so no additional database package is required.

## How to Run

1. Download or clone this repository.
2. Place `dataset_en_dev.json` in the same directory as the Python program.
3. Open the Python file in IDLE, VS Code, or another Python IDE.
4. Run the program.
5. Select option `1` from the menu to create the database and import the dataset.
6. Use the menu to perform the required database operations.

## CRUD Testing

The application was tested using:

- Insert operations to create new database records
- SQL `SELECT` statements to retrieve records
- Update operations to modify existing records
- Delete operations to remove review records by product category

## Technologies Used

- Python
- SQLite
- JSON
- SQL
- GitHub

## Author

Mason Ford
