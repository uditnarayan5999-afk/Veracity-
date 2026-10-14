from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import nlp_engine
import file_parser

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TextRequest(BaseModel):
    text: str

@app.post("/api/check")
async def check_endpoint(request: TextRequest):
    return nlp_engine.check_plagiarism(request.text)

@app.post("/api/check_file")
async def check_file_endpoint(file: UploadFile = File(...)):
    try:
        content = await file.read()
        extracted_text = file_parser.extract_text_from_file(content, file.filename)
        
        if not extracted_text or len(extracted_text.split()) < 3:
            raise HTTPException(status_code=400, detail="Could not extract enough readable text from the provided file.")
            
        return nlp_engine.check_plagiarism(extracted_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
