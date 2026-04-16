# Machining Time and Cost Estimation Web Application

A comprehensive web application for managing machining jobs, parts, and operations with real-time cost and time calculations.

## Features

- **Job Management**: Create, view, edit, and delete machining jobs
- **Part Management**: Add multiple parts to each job with material specifications
- **Operation Management**: Define different machining operations for each part
- **Real-time Calculations**: Automatic calculation of machining time and cost
- **Material Database**: Built-in material properties and machining parameters
- **Export Functionality**: Export job data to PDF and Excel formats
- **Responsive Design**: Works on desktop and mobile devices

## Tech Stack

- **Frontend**: HTML5, CSS3, JavaScript (ES6+), Bootstrap 5
- **Backend**: Python 3.9+, Flask
- **Database**: SQLite (development), MySQL/PostgreSQL (production)
- **APIs**: RESTful API with JSON
- **Authentication**: JWT (JSON Web Tokens)
- **Dependency Management**: pip/requirements.txt

## Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- MySQL or PostgreSQL (for production)
- Node.js and npm (for frontend development)

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/machining-calculator.git
   cd machining-calculator
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   # On Windows
   .\venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the root directory with the following content:
   ```env
   FLASK_APP=app.py
   FLASK_ENV=development
   SECRET_KEY=your-secret-key-here
   DATABASE_URL=sqlite:///machining.db
   ```

5. **Initialize the database**
   ```bash
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

6. **Run the application**
   ```bash
   flask run
   ```
   The application will be available at `http://localhost:5000`

## Project Structure

```
machining-calculator/
├── app/
│   ├── __init__.py         # Application factory
│   ├── models/             # Database models
│   │   ├── __init__.py
│   │   ├── job_models.py   # Job, Part, and Operation models
│   │   ├── material.py     # Material model
│   │   └── machining_parameter.py  # Machining parameters
│   │
│   ├── routes/             # Application routes
│   │   ├── __init__.py
│   │   ├── job_routes.py   # Job-related routes
│   │   ├── part_routes.py  # Part-related routes
│   │   └── operation_routes.py  # Operation-related routes
│   │
│   ├── static/             # Static files (CSS, JS, images)
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   │
│   └── templates/          # HTML templates
│       ├── base.html       # Base template
│       ├── jobs/           # Job-related templates
│       ├── parts/          # Part-related templates
│       └── operations/     # Operation-related templates
│
├── migrations/             # Database migrations
├── tests/                  # Test files
├── .env.example           # Example environment variables
├── .gitignore
├── config.py              # Configuration settings
├── requirements.txt       # Python dependencies
└── README.md              # This file
```

## API Documentation

The application provides a RESTful API for programmatic access. See the [API Documentation](API.md) for detailed information.

## Development

1. **Frontend Development**
   ```bash
   # Install frontend dependencies
   cd static
   npm install
   
   # Start development server
   npm run dev
   ```

2. **Running Tests**
   ```bash
   # Run all tests
   pytest
   
   # Run tests with coverage report
   pytest --cov=app
   ```

3. **Code Style**
   ```bash
   # Format code with Black
   black .
   
   # Lint code with flake8
   flake8 .
   ```

## Deployment

For production deployment, consider using:

1. **Web Server**: Nginx or Apache
2. **WSGI Server**: Gunicorn or uWSGI
3. **Process Manager**: Systemd or Supervisor
4. **Database**: MySQL or PostgreSQL

Example deployment with Gunicorn and Nginx:

```bash
# Install Gunicorn
pip install gunicorn

# Run the application with Gunicorn
gunicorn -w 4 -b 127.0.0.1:8000 "app:create_app()"
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Support

For support, please open an issue in the GitHub repository or contact the maintainers.

## Acknowledgments

- [Bootstrap](https://getbootstrap.com/) for the responsive UI components
- [Font Awesome](https://fontawesome.com/) for icons
- [Flask](https://flask.palletsprojects.com/) for the web framework
- [SQLAlchemy](https://www.sqlalchemy.org/) for the ORM
