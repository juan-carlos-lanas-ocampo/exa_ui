from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, Response
import httpx
from urllib.parse import quote

app = FastAPI()

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/91.0.4472.124 Safari/537.36"
    )
}

@app.get("/")
async def root():
    return {"message": "Proxy Server is running"}

@app.get("/proxy/")
async def proxy(url: str):
    try:
        # La URL ya debe venir correctamente codificada
        async with httpx.AsyncClient(headers=headers) as client:
            response = await client.get(url)

        response.raise_for_status()

        return Response(
            content=response.content,
            status_code=response.status_code,
            media_type=response.headers.get("content-type")
        )

    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Error al realizar la solicitud a {url}: {exc}"
        )

    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=exc.response.status_code,
            detail=f"Error HTTP {exc.response.status_code} al solicitar {url}"
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Error inesperado: {exc}"
        )

@app.get("/proxy_iframe/")
async def proxy_iframe(url: str):
    encoded_url = quote(url, safe='')

    return HTMLResponse(
        content=f'<iframe src="/proxy/?url={encoded_url}" width="100%" height="100%"></iframe>'
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
