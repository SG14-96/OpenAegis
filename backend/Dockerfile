FROM ubuntu:24.04

# install python and app dependencies
RUN apt-get update && apt-get install -y python3 python3-pip python3-venv build-essential libssl-dev libffi-dev python3-dev
COPY requirements.txt .
RUN pip3 install --break-system-packages -r requirements.txt

WORKDIR /app
COPY . .

ENV ENV_FILE=.env
CMD ["uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]
