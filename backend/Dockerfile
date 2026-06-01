FROM ubuntu:24.04

# install python and app dependencies
RUN apt-get update && apt-get install -y python3 python3-pip python3-venv build-essential libssl-dev libffi-dev python3-dev
COPY requirements.txt .
RUN pip3 install --break-system-packages -r requirements.txt

WORKDIR /app
COPY . .

# Install dependencies declared by each plugin
RUN find plugins -name requirements.txt \
    -exec pip3 install --break-system-packages -r {} \;

ENV ENV_FILE=.env
ENV PYTHONUNBUFFERED=1
CMD ["uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]
