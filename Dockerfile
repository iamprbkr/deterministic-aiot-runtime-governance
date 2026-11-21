FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir numpy pandas

# Copy governance code
COPY rerun_sil_experiments.py /app/
COPY scripts/ /app/scripts/

# Create results directory
RUN mkdir -p /app/results

# Default: run the harness
CMD ["python", "rerun_sil_experiments.py", "--seed", "42", "--output-dir", "/app/results"]