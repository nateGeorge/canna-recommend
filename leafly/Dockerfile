# Use an official Python runtime as a parent image
FROM python:3.7.1-slim-stretch

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install Firefox for scraping
RUN apt update
RUN apt install firefox-esr -y
# for running GUIs like firefox
RUN apt install libcanberra-gtk-module libcanberra-gtk3-module -y
RUN ./install_geckodriver.sh
RUN ./install_mongodb.sh

# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Run when the container launches
#CMD ["python", "scrape_leafly.py"]
