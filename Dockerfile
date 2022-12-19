# Docker file from Python 3.8.13
FROM python:3.8.13

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
ADD . /app

# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Make port 8080 available to the world outside this container
EXPOSE 8080

# Run streamlit when the container launches
CMD streamlit run LicensePlateRecognition.py --server.port 8080