FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the bot code and .env file
COPY bot.py .
COPY .env .

# Create a volume for persistent data
VOLUME ["/app/data"]

# Set environment variable for data file location
ENV DATA_FILE=/app/data/water_bot_data.json

# Run the bot
CMD ["python", "bot.py"]