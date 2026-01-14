FROM python:3.9

# Set working directory
WORKDIR /code

# Copy requirements
COPY requirements.txt /code/requirements.txt

# Install dependencies with TIMEOUT FIX
# Added --default-timeout=1000 to prevent timeout errors during build
RUN pip install --no-cache-dir --upgrade --default-timeout=1000 -r /code/requirements.txt

# Copy the rest of the application
COPY . .

# Create writable cache directory for Hugging Face
# This prevents permission errors when downloading models
RUN mkdir -p /code/cache && chmod -R 777 /code/cache
ENV TRANSFORMERS_CACHE=/code/cache
ENV HF_HOME=/code/cache

# Open the port Hugging Face expects
EXPOSE 7860

# Run the app
CMD ["python", "run.py"]