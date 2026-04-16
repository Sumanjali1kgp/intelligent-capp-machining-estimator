
### Machining Process Planning and Cost Estimation

---

## Overview

This project presents an intelligent **Computer-Aided Process Planning (CAPP)** system developed for the Central Workshop and Instrument Service Section (CWISS), IIT Kharagpur.

The system transforms traditional **manual, experience-based machining estimation** into a **data-driven, automated, and standardized workflow** for computing machining time and cost.

---

## Key Features

### Phase I (Foundation)

* Web-based machining time & cost estimator
* Database-driven parameter selection (feed, speed, depth of cut)
* Multi-operation support (Turning, Drilling, Boring, Grooving)
* Automated report generation (Workshop & Customer)

### Phase II (Enhancements)

* Constraint-based validation system (ensures feasible machining conditions)
* Intelligent warning system for unsafe inputs
* Cost visualization (interactive breakdown charts)
* Job storage & duplication (variant-based planning)
* Improved UI/UX for workshop usability

---

## System Architecture

* **Frontend:** HTML, CSS, JavaScript (Bootstrap)
* **Backend:** Flask (Python)
* **Database:** SQLite with SQLAlchemy ORM
* **Design:** Modular operation-based architecture

---

## Core System Logic

* Workflow: **Job → Part → Operation**
* Each operation is computed independently
* Parameters selected dynamically from database
* Time and cost aggregated across operations

---

## Cost Components

* Machining Cost
* Setup & Idle Cost
* Tooling Cost
* Material Cost
* Overhead Cost

---



## Key Contributions

* Standardized machining estimation workflow
* Unified parameter mapping across operations
* Modular operation-level computation system
* Integrated validation and decision-support features

---

## Future Scope

* CAD integration for automatic feature recognition
* Machine learning-based parameter optimization
* Cloud-based deployment and analytics dashboard

---

## References

* Machining Data Handbook
* Kalpakjian & Schmid – Manufacturing Processes
* PSG Design Data Book
* Flask, SQLite Documentation

---

## Author

**Sumanjali Chinnadandluru**
IIT Kharagpur

---

## 📜 License

MIT License

