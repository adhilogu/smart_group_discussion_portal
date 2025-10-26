
# Smart Group Discussion Platform

The **Smart Group Discussion (GD) Platform** is a web-based system designed to automate and streamline group discussions for academic, recruitment, and training purposes. It addresses common issues such as **dominance, bias, and lack of transparency** in tradnnnitional GD formats by introducing **QR-based authentication, automated topic allocation, structured turn-taking, and peer evaluation mechanisms**.  

The platform integrates **Django (backend), React (frontend), PostgreSQL (database)** and ensuring scalability, security, and real-time performance. A custom **Bias-Filtered Weighted Rank Aggregation (BF-WRA)** algorithm is implemented to detect biased voting and normalize peer evaluation, guaranteeing fairness and accuracy in results.  


## Features

- **QR-based Authentication** → Prevents proxy entries and ensures secure participation.  
- **Random Topic Allocation** → Eliminates manual bias in topic selection.  
- **Turn-Based Participation** → Prevents dominance and ensures balanced contributions.  
- **Peer Voting & Evaluation Dashboards** → Structured ranking for fairness.  
- **Bias Detection (BF-WRA Algorithm)** → Identifies manipulative or biased voting.  
- **PostgreSQL Secure Logging** → Stores session data for analytics and traceability.  
- **Real-Time Results** → Instant evaluation and leaderboard generation.  



## Workflow of the project

![image](git-images/wflow.png)


## Tech Stack
- **Frontend**: React, Bootstrap  
- **Backend**: Django, Django REST Framework  
- **Database**: PostgreSQL  
- **Authentication**: QR Code Integration  
- **Version Control**: GitHub  
- **Algorithm**: BF-WRA (Bias-Filtered Weighted Rank Aggregation)  


## Project Setup

Run the following command

**Step 1: Clone the Repository**

```bash
#Clone the Project 
git clone https://github.com/adhilogu/smart_group_discussion_portal.git


# Navigate to Django directory 
cd django-datta-able 

# Create virtual environment (recommended) 
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure database settings in settings.py
# Update DATABASES configuration with your PostgreSQL
credentials
```

**Step 2: Project setup**
```bash
# Run migrations
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic
```

```bash
# Create superuser (admin)
python manage.py createsuperuser


# Create ssl certificate
pip install django-extensions Werkzeug pyOpenSSL

# Generate a private key
openssl genrsa -out key.pem 2048

# Generate a certificate signing request (CSR).
openssl req -new -key key.pem -out csr.pem

# Add django_extensions to INSTALLED_APPS in your settings.py
    INSTALLED_APPS = [
        # ... other apps
        'django_extensions',
    ]

```

**Step 3: Start development server**
```bash
python manage.py runserver_plus 8000 --cert-file cert.pem  
```

At this point, the app runs at https://127.0.0.1:8000/

Admin panel at  https://127.0.0.1:8000/admin

## [Snapshots of the project]

![image](git-images/adminpanel.png)
Admin Panel



![image](git-images/slots.png)
Creating a slot

![image](git-images/groups.png)
![image](git-images/creatinggroup.png)
Creating groups inside slots


![image](git-images/qr.png)
Showing qr code to join the group

![image](git-images/cam.png)
Joining the group via qr code scanning

![image](git-images/pause.png)
Host Waiting for minimum 6 members to join a grop


![image](git-images/joining.png)
![image](git-images/joiningstatus.png)
Group started

![image](git-images/speaking.png)
Members in group discusion Speaking

![image](git-images/reqvoting.png)
Members in group discusion requesting for voting


![image](git-images/voting.png)
Voting

![image](git-images/posresult.png)
![image](git-images/negresult.png)
Voting results
## Support
![LOGO](git-images/techsagalogo.png)
For support, email adhilogu2004@gmail.com


[![linkedin](https://img.shields.io/badge/linkedin-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/adithya-loganathan-a47218283/)

[![instagram](https://img.shields.io/badge/instagram-E4405F?style=for-the-badge&logo=instagram&logoColor=white)](https://www.instagram.com/adithyaloganathanh/?hl=en)

[![github](https://img.shields.io/badge/github-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/adhilogu)

