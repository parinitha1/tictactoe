# Use an official lightweight Python image
FROM python:3.11.4  

# Set the working directory
WORKDIR /app  

# Copy project files into the container
COPY . /app  

# Install dependencies
RUN pip install -r requirements.txt  

# Expose port 5000 for Flask
EXPOSE 8001  

# Command to run the app
CMD python app.py


