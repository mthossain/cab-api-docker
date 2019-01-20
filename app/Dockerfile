FROM python:3.6

EXPOSE 5000

WORKDIR /app

COPY requirements.txt /app
RUN pip install -r requirements.txt

COPY templates /app/
COPY templates/home.html /app/templates/
COPY templates/error.html /app/templates/
COPY app.py /app
CMD python app.py
