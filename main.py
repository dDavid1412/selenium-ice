from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session
from config import models
from config import database
from config import schemas

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/games")
def verJuegos(
    db: Session = Depends(get_db),
) -> list[schemas.GameResponse]:
    juegos = db.query(models.Game).all()
    return juegos

@app.post("/games")
def agregarJuego(
    juego: schemas.GameCreate,
    db: Session = Depends(get_db),
) -> schemas.GameResponse:
    nuevo_juego = models.Game(**juego.model_dump())
    db.add(nuevo_juego)
    db.commit()
    db.refresh(nuevo_juego)
    return nuevo_juego

@app.put("/games/{juego_id}")
def actualizarJuego(
    juego_id: int,
    juego: schemas.GameCreate,
    db: Session = Depends(get_db),
) -> schemas.GameResponse:
    juego_existente = db.query(models.Game).filter(models.Game.id == juego_id).first()
    if not juego_existente:
        raise HTTPException(status_code=404, detail="Juego no encontrado")
    for key, value in juego.model_dump().items():
        setattr(juego_existente, key, value)
    db.commit()
    db.refresh(juego_existente)
    return juego_existente

@app.delete("/games/{juego_id}")
def eliminarJuego(
    juego_id: int,
    db: Session = Depends(get_db),
):
    juego_existente = db.query(models.Game).filter(models.Game.id == juego_id).first()
    if not juego_existente:
        raise HTTPException(status_code=404, detail="Juego no encontrado")
    db.delete(juego_existente)
    db.commit()
    return {"message": "Juego eliminado exitosamente"}

@app.patch("/games/{juego_id}")
def actualizarPrecioJuego(
    juego_id: int,
    nuevo_precio: int,
    db: Session = Depends(get_db),
) -> schemas.GameResponse:
    juego_existente = db.query(models.Game).filter(models.Game.id == juego_id).first()
    if not juego_existente:
        raise HTTPException(status_code=404, detail="Juego no encontrado")
    juego_existente.price = nuevo_precio
    db.commit()
    db.refresh(juego_existente)
    return juego_existente