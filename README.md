## Swahili Speech-Based Community Concern Classification

**Student:** Obonyo Paul Rapando  
**Admission Number:** 169688  
**Supervisor:** Dr. Joseph Onderi Orero, PhD  
**Institution:** Strathmore University, School of Computing and Engineering Sciences

### Project Overview

This system allows residents of Mathare Informal Settlement, Nairobi, to report community concerns verbally in Swahili through a mobile application. The spoken input is transcribed using Whisper, converted into contextual embeddings using AfroXLMR, and classified into one of four service categories — Food Security, Health, Shelter, or Safety — using a trained XGBoost model. Classified concerns are automatically routed to the registered CBO for that category.

### Repository Structure

PaulObonyo_169688/
├── backend/ Flask API, Whisper transcription, AfroXLMR embedding, XGBoost classification
├── mobile/ React Native mobile application for Mathare residents
├── dashboard/ React.js CBO dashboard for real-time concern monitoring
├── data/ Raw corpus files, processed text, annotated training data
├── models/ Saved trained XGBoost model files
├── notebooks/ Jupyter notebooks for data exploration and model training (run on Google Colab)
├── scripts/ Standalone automation scripts
└── docs/ Project proposal and diagrams


### Dataset

Primary training data: Masasi, N., & Masua, B. (2024). Swahili Corpus. Mendeley Data.  
https://data.mendeley.com/datasets/d4yhn5b9n6/2

### Setup Instructions

#### 1. Clone the repository
```bash
git clone <your-repo-url>
cd PaulObonyo_169688
```

#### 2. Set up the Python backend environment
```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

#### 3. Configure environment variables
```bash
cp .env.example .env
# Open .env and fill in database credentials
```

#### 4. Set up the database
```bash
make setup-db
```

#### 5. Run the backend
```bash
make run-backend
```

#### 6. Run the dashboard
```bash
make run-dashboard
```

#### 7. Run the mobile app
```bash
make run-mobile
```

### ML Notebooks

The notebooks in the notebooks/ folder will run on Colab with GPU acceleration.  
Upload the notebook to Colab, mount Google Drive, and run all cells.
