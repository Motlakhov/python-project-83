### Hexlet tests and linter status:
[![Actions Status](https://github.com/Motlakhov/python-project-83/actions/workflows/hexlet-check.yml/badge.svg)](https://github.com/Motlakhov/python-project-83/actions)

[![Maintainability](https://api.codeclimate.com/v1/badges/f95e5efcb06b832fe962/maintainability)](https://codeclimate.com/github/Motlakhov/python-project-83/maintainability)

# Page Analyzer

Page Analyzer is a Flask web application that allows users to analyze web pages for SEO effectiveness. The application checks the availability of websites and analyzes elements such as headers, descriptions, and H1 tags.

## Features

- URL availability check.
- Analysis of title and description tags.
- Display of check results on the user interface.

## Demo

You can view the application in action at this link:
[python-project-83-s8pp.onrender.com](https://python-project-83-s8pp.onrender.com)

## Technologies

- Python
- Flask
- PostgreSQL
- HTML/CSS
- Bootstrap for frontend
- Poetry for dependency management

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

Ensure you have Python, Poetry, and PostgreSQL installed.

### Installation and Running

Use the `Makefile` to simplify the installation and startup process:

```bash
git clone https://github.com/Motlakhov/python-project-83
cd python-project-83

## Configuration
Before running the application, make sure your environment variables are set up correctly. Check the .env file and ensure that it contains valid values for the following variables:
SECRET_KEY: A secret key for your application.
DATABASE_URL: The connection string for your PostgreSQL database, formatted as postgresql://username:password@localhost:5432/database_name.

# Install dependencies
make install

# Run the local development server
make dev

# Run the production server
make start
```

### Testing

To run tests, use the following command:

```bash
make lint  # Code linting
```