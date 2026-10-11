FROM python:3.11-slim
WORKDIR /backend
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PORT=10000
EXPOSE 8000
EXPOSE 10000
CMD ["python", "start.py"]
