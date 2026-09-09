FROM python:3.12

# Set the working directory
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . ./

# Install the required dependencies
RUN pip install -r requirements.txt

# Make port 8080 available to the world outside this container
EXPOSE 8080
ENV PORT=8080

# Serve with gunicorn, not Flask's dev server -- the dev server's debugger
# allows arbitrary code execution if it's ever reachable in production.
CMD exec gunicorn --bind 0.0.0.0:${PORT} main:app