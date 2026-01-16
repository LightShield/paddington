# Dockerfile for pahole testing
FROM ubuntu:22.04

# Install pahole (part of dwarves package)
RUN apt-get update && \
    apt-get install -y \
    dwarves \
    build-essential \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt requirements-dev.txt /tmp/
RUN pip3 install -r /tmp/requirements.txt -r /tmp/requirements-dev.txt

# Set working directory
WORKDIR /paddington

# Default command
CMD ["/bin/bash"]
