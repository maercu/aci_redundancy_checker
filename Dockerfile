FROM python:3-alpine

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY test_redundancy.py .

CMD [ "python", "test_redundancy.py" ]
