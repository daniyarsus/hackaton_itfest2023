FROM python:3.9-slim

WORKDIR /app

# Install pip version 23.0.1
RUN python -m pip install --upgrade pip==23.0.1

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the rest of the application code
COPY . .

# Specify the command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
