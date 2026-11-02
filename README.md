# VoltWise – Smart Electricity Consumption and Optimization System

## 1. Project Overview

VoltWise is a web-based electricity consumption monitoring and optimization system developed using Python Flask. It helps users monitor electricity usage, generate and predict electricity bills, analyze appliance consumption and receive electricity-saving suggestions.

The system also supports meter image processing using OpenCV and Tesseract OCR to extract meter readings.

## 2. Features

- User Registration and Login
- Electricity Bill Generation
- Electricity Bill Prediction
- Appliance Consumption Analysis
- Weekly and Monthly Usage Graphs
- Electricity-Saving Suggestions
- Meter Image Upload and OCR Processing

## 3. Technologies Used

| Technology | Purpose |
|---|---|
| HTML, CSS, JavaScript | Frontend development |
| Chart.js | Graph visualization |
| Python Flask | Backend development |
| SQLite | Database |
| OpenCV | Image processing |
| Tesseract OCR | Meter reading extraction |
| Git and GitHub | Version control |
| Docker and Docker Compose | Containerization and deployment |
| Selenium | Browser automation testing |
| Python unittest | Application testing |
| Prometheus and Grafana | Monitoring |

## 4. Project Structure

```text
electricity-consumption/
│
├── app.py
├── templates/
├── static/
├── tests/
├── monitoring/
│   └── prometheus.yml
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .gitignore
└── README.md
```

## 5. Installation and Setup

### Step 1: Clone the Repository

```bash
git clone https://github.com/Irfana-09/devops-project.git
```

### Step 2: Navigate to the Project Folder

```bash
cd devops-project/electricity-consumption
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

Make sure Python, Tesseract OCR and the required image-processing dependencies are installed.

## 6. Run the Application Locally

```bash
python app.py
```

Open the browser and visit:

```text
http://localhost:5000
```

## 7. Testing

### Python Unit Testing

Run all Python unit tests using:

```bash
python -m unittest discover -s tests -v
```

### Selenium Browser Testing

Make sure the VoltWise application is running before executing the Selenium test.

```bash
python -m unittest tests.test_login -v
```

Selenium WebDriver opens Chrome and checks the login form's empty-field validation.

## 8. Docker Deployment

### Build Docker Image

```bash
docker build -t voltwise:1.0 .
```

### Run Docker Container

```bash
docker run -d --name voltwise-app -p 5000:5000 voltwise:1.0
```

### Check Running Containers

```bash
docker ps
```

### Access the Application

```text
http://localhost:5000
```

## 9. Docker Compose

To start the monitoring services defined in the Docker Compose configuration:

```bash
docker compose up -d prometheus grafana
```

Use the following addresses to access the monitoring tools:

- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000

## 10. Monitoring

Prometheus is configured to scrape its own metrics endpoint at 15-second intervals. Grafana is connected to Prometheus as a data source to visualize the available metrics.

## 11. Future Enhancements

- Cloud deployment
- Advanced electricity consumption analytics
- Improved automated browser testing
- Extended application monitoring

## 12. Project Repository

GitHub: https://github.com/Irfana-09/devops-project

**Project Name:** VoltWise – Smart Electricity Consumption and Optimization System
