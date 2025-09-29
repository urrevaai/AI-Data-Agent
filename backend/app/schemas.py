from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class UploadResponse(BaseModel):
    upload_id: str
    message: str
    file_name: str
    schema: Dict[str, List[Dict[str, str]]]

class QueryRequest(BaseModel):
    upload_id: str
    question: str

class VisualizationSuggestion(BaseModel):
    chart_type: Optional[str] = 'table'
    x_axis: Optional[str] = None
    y_axis: Optional[List[str]] = None
    title: Optional[str] = "Query Result"

class QueryResponse(BaseModel):
    natural_language_answer: str
    query_result_data: List[Dict[str, Any]]
    visualization_suggestion: VisualizationSuggestion