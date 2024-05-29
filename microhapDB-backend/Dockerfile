#Base image
FROM python:3.12-slim

#Set working directory
WORKDIR /code/

# Install system dependencies
RUN apt-get update && apt-get install -y libpq-dev gcc

# Install Python dependencies
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
RUN pip install psycopg2-binary  # Adding psycopg2-binary for PostgreSQL support

#Copy source code and templates
COPY ./src /code/src
COPY ./templates /code/templates

# Create a directory to hold the uploaded files
RUN mkdir /code/temp


#Command to run application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]