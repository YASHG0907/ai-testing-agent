from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {"message": "AI Testing Agent Running"}

@app.get("/run-test")
def run_test():
    return {"status": "Test executed successfully"}