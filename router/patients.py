from typing import List

from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload
from fastapi import FastAPI, Depends, HTTPException, APIRouter
from router.auth import get_current_user, get_user_exception
import model
from database import Base, engine, SessionLocal
from router.doctors import  doctor_response

router = FastAPI()

model.Base.metadata.create_all(bind=engine)


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


router = APIRouter(
    prefix="/patients",
    responses={404: {"description": "Not found"}}
)


class ui_patient(BaseModel):
    name: str
    age: int
    disease: str
    room_id: int


class patient_response(BaseModel):
    id:int
    name: str
    age: int
    disease: str
    room_id: int

    class Config:
        orm_mode = True


class patient_schema(patient_response):
    doctor: List[doctor_response]


@router.get("/", tags=["patients"],response_model=List[patient_schema])
async def get_all_patients(db: Session = Depends(get_db)):
    patient = db.query(model.Patients)\
        .options(joinedload(model.Patients.doctor))\
        .all()

    return patient


@router.get("/{patient_id}", tags=["patients"],response_model=patient_schema)
async def get_patient_byid(patient_id: int, db: Session = Depends(get_db)):
    req_post = db.query(model.Patients)\
        .options(joinedload(model.Patients.doctor))\
        .filter(patient_id == model.Patients.id).all()
    if not req_post:
        return get_notfound_exception()
    return req_post


@router.post("/", tags=["patients"])
async def add_new_patient(patient: ui_patient, db: Session = Depends(get_db), adm: dict = Depends(get_current_user)):
    if not adm:
        return get_user_exception
    patient_model = model.Patients()
    patient_model.name = patient.name
    patient_model.age = patient.age
    patient_model.disease = patient.disease
    patient_model.room_id = patient.room_id
    db.add(patient_model)
    db.commit()

    return successful_response(201)


@router.put("/", tags=["patients"])
async def edit_patient_details(id: int, patient: ui_patient, db: Session = Depends(get_db),
                               adm: dict = Depends(get_current_user)):
    if not adm:
        return get_user_exception()

    req_post = db.query(model.Patients).filter(id == model.Patients.id).first()
    if not req_post:
        return get_notfound_exception()
    req_post.name = patient.name
    req_post.age = patient.age
    req_post.disease = patient.disease
    req_post.room_id = patient.room_id
    db.commit()

    return successful_response(201)


@router.delete("/", tags=["patients"])
async def delete_patient_details(id: int, db: Session = Depends(get_db), adm: dict = Depends(get_current_user)):
    if not adm:
        return get_user_exception()
    req_post = db.query(model.Patients).filter(id == model.Patients.id).first()
    if not req_post:
        return get_notfound_exception()
    db.query(model.Patients).filter(id == model.Patients.id).delete()
    db.query(model.link).filter(id==model.link.patient_id).delete()

    db.commit()

    return successful_response(201)


@router.post("/doc", tags=["patients"])
async def assign_patients(patient_id: int, doc_id: int, db: Session = Depends(get_db),
                          adm: dict = Depends(get_current_user)):
    if not adm:
        return get_user_exception()
    req_patient = db.query(model.Patients).filter(patient_id == model.Patients.id).first()
    if not req_patient:
        return get_notfound_exception()
    link_value = model.link()
    link_value.patient_id = patient_id
    link_value.doctors_id = doc_id

    db.add(link_value)
    db.commit()

    return successful_response(201)


def get_notfound_exception():
    HTTPException(status_code=201,
                  detail="Entry not found")


def successful_response(status_code):
    return {
        "status_response": status_code,
        "details": "Successful"
    }
