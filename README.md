# AI Data Agent

A full-stack application that allows users to upload Excel files and query them using natural language. The backend uses AI (Google Gemini) to convert questions into SQL queries, and the frontend provides an intuitive interface for data visualization.

## Features

- 📊 **Excel File Upload**: Upload Excel files with multiple sheets
- 🤖 **AI-Powered Queries**: Ask questions in natural language
- 🔍 **Smart SQL Generation**: AI converts questions to optimized SQL queries
- 📈 **Data Visualization**: Automatic chart generation (bar, line, pie, table)
- 🛡️ **AI Guardrails**: Self-correcting SQL with error handling
- 🗄️ **PostgreSQL Support**: Built for Neon PostgreSQL database

## Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - Database ORM
- **Google Gemini AI** - Natural language to SQL conversion
- **Pandas** - Data processing and Excel handling
- **PostgreSQL** - Database (via Neon)

### Frontend
- **React** - UI framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **Recharts** - Data visualization
- **Vite** - Build tool

## Prerequisites

- Python 3.8+
- Node.js 16+
- PostgreSQL database (Neon recommended)

## Setup Instructions

### 1. Clone the Repository

```bash
git clone <repository-url>
cd data2
```

### 2. Backend Setup

```bash
cd backend
pip install -r requirements.txt
```

Create a `.env` file in the `backend` directory:

```env
GEMINI_API_KEY=your_gemini_api_key_here
DATABASE_URL=postgresql+psycopg2://user:password@host:5432/dbname
```

### 3. Frontend Setup

```bash
cd frontend
npm install
```

### 4. Database Setup

1. Create a PostgreSQL database (Neon, Supabase, or local)
2. Update the `DATABASE_URL` in your `.env` file
3. The application will automatically create tables when you upload data

## Running the Application

### Start the Backend

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Start the Frontend

```bash
cd frontend
npm run dev
```

The application will be available at:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000

## Usage

1. **Upload Data**: Click "Upload Excel File" and select your Excel file
2. **Ask Questions**: Type natural language questions about your data
3. **View Results**: See both the data and automatically generated visualizations

### Example Questions

- "What are the total sales by month?"
- "Show me the top 5 products by revenue"
- "What's the average rating by category?"
- "Compare sales between regions"

## API Endpoints

- `POST /upload` - Upload Excel file
- `POST /query` - Submit natural language query
- `GET /` - Health check

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GEMINI_API_KEY` | Google Gemini API key | Yes |
| `DATABASE_URL` | PostgreSQL connection string | Yes |

### AI Model Configuration

The application uses Google Gemini 2.5 Flash by default. You can modify the model in `backend/app/services.py`:

```python
model_name = "models/gemini-2.5-flash-preview-05-20"
```

## Deployment

### Backend (Render, Railway, etc.)

1. Set environment variables in your deployment platform
2. Ensure `DATABASE_URL` points to your production database
3. Deploy the `backend` directory

### Frontend (Vercel, Netlify, etc.)

1. Build the frontend: `npm run build`
2. Deploy the `dist` folder
3. Update API endpoints to point to your backend URL

## Troubleshooting

### Common Issues

1. **"Gemini model not found"**: Update the model name in `services.py`
2. **SQL errors**: The AI will automatically retry with corrected queries
3. **Upload failures**: Check file format (Excel only) and size limits
4. **Database connection**: Verify `DATABASE_URL` format and credentials