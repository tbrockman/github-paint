FROM python:3.12

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN ls -R /app

ENTRYPOINT [ "python", "-m", "src.main" ]