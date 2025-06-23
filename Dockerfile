FROM python:3.11.5
RUN apt update && apt upgrade -y

# Installa dipendenze di sistema
LABEL authors="SoNicItconsulting"

RUN pip install --upgrade pip

WORKDIR /app
COPY *.py /app
COPY requirements.txt /app

RUN pip install -r requirements.txt

ENTRYPOINT ["python", "sonic_mail_agent_main.py"]
