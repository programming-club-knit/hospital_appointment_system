from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.database import get_db
from app.models import Appointment, Doctor, Patient
from app.schemas import AppointmentCreate, AppointmentRead, AppointmentReschedule

router = APIRouter(prefix="/appointments", tags=["Appointments"])


@router.post("", response_model=AppointmentRead, status_code=201)
def book_appointment(payload: AppointmentCreate, db: Session = Depends(get_db)):
    doctor = db.get(Doctor, payload.doctor_id)
    patient = db.get(Patient, payload.patient_id)
    if doctor is None:
        raise HTTPException(status_code=404, detail="Doctor not found")
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")

    existing = db.scalar(
        select(Appointment).where(
            Appointment.doctor_id == payload.doctor_id,
            Appointment.appointment_time == payload.appointment_time,
            Appointment.status == "booked",
        )
    )
    if existing:
        raise HTTPException(status_code=409, detail="This time is already booked")

    appointment = Appointment(
        patient_id=payload.patient_id,
        doctor_id=payload.doctor_id,
        appointment_time=payload.appointment_time,
        fee=doctor.consultation_fee,
        status="booked",
    )
    
    current_time = datetime.now()
    
    if appointment.appointment_time<current_time:
        raise HTTPException(status_code=422, detail="This date is passed")
    #issue 3
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return appointment


@router.get("", response_model=list[AppointmentRead])
def list_appointments(
    patient_id: int | None = Query(default=None),
    skip: int = 0,
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = select(Appointment)
    if patient_id is not None:
        query = query.where(Appointment.patient_id == patient_id)

    return db.scalars(
        query.order_by(Appointment.appointment_time).offset(skip).limit(limit)
    ).all()


@router.patch("/{appointment_id}/cancel", response_model=AppointmentRead)
def cancel_appointment(appointment_id: int, db: Session = Depends(get_db)):
    appointment = db.get(Appointment, appointment_id)
    if appointment is None:
        raise HTTPException(status_code=404, detail="Appointment not found")
    if appointment.status != "booked":
        raise HTTPException(status_code=409, detail="Only booked appointments can be cancelled")

    appointment.status = "cancelled"
    # Intentional issue B1: cancellation is not committed to the database.
    # issue 5
#hello

    db.commit()
    db.refresh(appointment)
    return appointment


@router.patch("/{appointment_id}/reschedule", response_model=AppointmentRead)
def reschedule_appointment(
    appointment_id: int,
    payload: AppointmentReschedule,
    db: Session = Depends(get_db),
):
    appointment = db.get(Appointment, appointment_id)
    if appointment is None:
        raise HTTPException(status_code=404, detail="Appointment not found")

    # Intentional issue B5: does not check if the target time is already booked.
    appointment.appointment_time = payload.appointment_time
    db.commit()
    db.refresh(appointment)
    return appointment


@router.patch("/{appointment_id}/status", response_model=AppointmentRead)
def update_status(
    appointment_id: int,
    status: str,
    db: Session = Depends(get_db),
):
    appointment = db.get(Appointment, appointment_id)
    if appointment is None:
        raise HTTPException(status_code=404, detail="Appointment not found") #issue 2 solved

    # Intentional issue C2: caller can alter any appointment because there is no
    # patient identity/authorization check in this educational starter.
    appointment.status = status
    db.commit() 
    db.refresh(appointment)
    return appointment
