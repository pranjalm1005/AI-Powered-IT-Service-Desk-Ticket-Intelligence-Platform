<img width="1457" height="775" alt="image" src="https://github.com/user-attachments/assets/747d2d1c-02aa-4d97-af78-c2e962d0e31a" /># 🤖 AI-Augmented IT Support & Ticketing System

An intelligent IT Service Management (ITSM) platform that automates ticket classification, similarity search, and resolution recommendations using Machine Learning, Vector Search, and Generative AI on AWS.

---

## 📌 Overview

This project is an end-to-end AI-powered helpdesk system that:

* Classifies incoming IT tickets using NLP
* Finds similar historical issues using embeddings
* Generates AI-based resolution suggestions and IT summaries
* Provides a web-based Admin & User portal
* Runs fully serverless on AWS (Lambda + Bedrock + DynamoDB)

---

## 🧠 Key Features

* 🔍 **Automatic Ticket Classification** (ML + Sentence Transformers)
* 📊 **Semantic Similarity Search** (Vector Embeddings)
* 🤖 **AI Resolution Suggestion** (Amazon Bedrock / LLM)
* 🧑‍💻 **User Portal** to raise and track tickets
* 🛠 **Admin Dashboard** with analytics & status management
* ☁ **Serverless Architecture** using AWS Lambda & DynamoDB

---

## 🏗 Architecture

```
Streamlit UI
     |
API Gateway
     |
AWS Lambda (Microservices)
     |
DynamoDB  +  Bedrock (LLM)
     |
ML Embeddings (SentenceTransformers)
```

---

## 📁 Project Structure

```
ai-itsm-platform/
├── ui/                 # Streamlit Frontend
├── lambdas/            # All backend Lambda functions
├── ml/                 # Training & Embedding models
├── infrastructure/    # IAM, DynamoDB schema, deployment notes
├── screenshots/       # UI screenshots
├── README.md
├── requirements.txt
```

---

## ⚙️ Technologies Used

* **Frontend:** Streamlit, Python
* **Backend:** AWS Lambda, API Gateway
* **Database:** AURORA RDS
* **AI / ML:**

  * SentenceTransformers
  * Scikit-Learn
  * Amazon Bedrock (LLM)
* **Vector Search:** Semantic embeddings
* **Cloud:** AWS (IAM, S3, CloudWatch)

---

## 🚀 How to Run Locally

```bash
git clone https://github.com/yourname/ai-itsm-platform
cd ui
pip install -r requirements.txt
streamlit run app.py
```

---

---

## 🧩 Lambda Functions

| Function                  | Purpose                    |
| ------------------------- | -------------------------- |
| classify_ticket_lambda    | Predicts ticket category   |
| search_similar_tickets    | Vector similarity search   |
| create_ticket_lambda      | Stores ticket in DynamoDB  |
| get_resolution_suggestion | Bedrock AI solution        |
| generate_it_summary       | LLM-based incident summary |

---

## 🎯 Use Cases

* Enterprise IT Helpdesk Automation
* AI-Powered Support Assistants
* Incident Resolution Knowledge Systems
* NLP-based Ticket Analytics

---

## 👨‍💻 Author

**Pranjal Mahapatra**
AI / Cloud / Data Engineering
LinkedIn | GitHub

---

This repository demonstrates a production-style, cloud-native AI system combining NLP, LLMs, and serverless architecture for intelligent IT operations.
