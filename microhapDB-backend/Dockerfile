#Base image
FROM python:3.11-slim

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

# Create a directory for temporary files in /tmp which is more container-friendly
RUN mkdir -p /tmp/microhap && chmod 777 /tmp/microhap
ENV TEMP_UPLOAD_DIR=/tmp/microhap

# Set environment variables for better container behavior
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

EXPOSE 80
#Command to run application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "80"]