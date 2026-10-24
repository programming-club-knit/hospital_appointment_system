from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.database import get_db
from app.models import Doctor, Patient
from app.schemas import DoctorCreate, DoctorRead, PatientCreate, PatientRead

router = APIRouter(tags=["Doctors and Patients"])

@router.post("/doctors", response_model=DoctorRead, status_code=status.HTTP_201_CREATED)

def create_doctor(payload: DoctorCreate, db: Session = Depends(get_db)):
    doctor = Doctor(**payload.model_dump())
    db.add(doctor)
    db.commit()
    db.refresh(doctor)
    return doctor


@router.get("/doctors", response_model=list[DoctorRead])
def list_doctors(specialization: str | None = None, db: Session = Depends(get_db)):
    query = select(Doctor)
    if specialization:
        query = query.where(Doctor.specialization == specialization)
    return db.scalars(query.order_by(Doctor.name)).all()


@router.get("/doctors/{doctor_id}", response_model=DoctorRead)
def get_doctor(doctor_id: int, db: Session = Depends(get_db)):
    doctor = db.get(Doctor, doctor_id)

    if doctor is None:
        raise HTTPException(status_code=404, detail=" The Requested doctor does not exist")
 
    return doctor


@router.post("/patients", response_model=PatientRead, status_code=201)
def create_patient(payload: PatientCreate, db: Session = Depends(get_db)):
    patient = Patient(**payload.model_dump())
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient
