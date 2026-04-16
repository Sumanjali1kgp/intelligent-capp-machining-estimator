# Intelligent CAPP-Based Machining Time and Cost Estimator

## Overview

This project presents a web-based **Computer-Aided Process Planning (CAPP)** system developed as part of a Bachelor Thesis Project at IIT Kharagpur.

The system automates machining time and cost estimation by replacing traditional manual calculations with a structured, data-driven approach.

It is designed to support workshop environments such as CWISS (Central Workshop & Instrument Service Section).

---

## Key Features

### Core Functionality

* Job → Part → Operation workflow
* Multi-operation support:

  * Turning
  * Drilling
  * Boring
  * Grooving
  * Milling
* Automatic machining time calculation
* Cost estimation based on machining parameters

### Advanced Features (BTP Phase II)

* Constraint-based validation (safe machining conditions)
* Intelligent warnings for invalid inputs
* Cost breakdown visualization
* Job saving and duplication
* PDF report generation (customer & shop floor)

---

## Tech Stack

* **Frontend:** HTML, CSS, JavaScript (Bootstrap)
* **Backend:** Flask (Python)
* **Database:** SQLite (SQLAlchemy ORM)

---

## System Architecture

The system follows a modular design:

* Each machining operation is modeled independently
* Parameters (feed, speed, depth of cut) are selected dynamically
* Total machining time and cost are aggregated across operations

---

## Project Structure

```
├── app.py                 # Main Flask application
├── models/               # Machining operation models
├── routes/               # API and UI routes
├── static/              # CSS, JS, images
├── templates/           # HTML templates
├── setup_database.py    # Database initialization
├── requirements.txt     # Dependencies
└── test_api.py          # Basic testing
```

---

## Installation & Setup

```bash
# Clone repository
git clone https://github.com/Sumanjali1kgp/intelligent-capp-machining-estimator.git
cd intelligent-capp-machining-estimator

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
python setup_database.py

# Run application
python app.py
```

Access the app at:
http://localhost:5000

---

## Cost Components Considered

* Machining Cost
* Setup Cost
* Tooling Cost
* Material Cost
* Overhead Cost

---

## Key Contributions

* Developed a structured CAPP workflow for machining estimation
* Integrated database-driven machining parameters
* Designed modular operation-based computation system
* Implemented validation and decision-support features

---

## Future Scope

* CAD-based feature recognition
* Machine learning for parameter optimization
* Cloud deployment for multi-user access

---

## References

* Machining Data Handbook
* PSG Design Data Book
* Kalpakjian – Manufacturing Engineering

---

## Author

**Sumanjali Chinnadandluru**
IIT Kharagpur
