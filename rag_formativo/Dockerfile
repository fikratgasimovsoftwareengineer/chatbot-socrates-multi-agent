# Use an official Python runtime as a base image
# DOCKER FILE PER IL SVILUPPO
FROM python:3.10


# Install system dependencies
RUN apt-get update && apt-get install -y \
    libportaudio2 \
    libportaudiocpp0 \
    portaudio19-dev \
    libasound-dev \
    alsa-utils \
    pulseaudio


# Set the working directory inside the container
WORKDIR /app

# Copy requirements.txt and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port your app runs on (change if needed)
EXPOSE 5000

# Command to run the application
CMD ["python3", "rag_formativo_socrates.py"]
