from fastapi import FastAPI, HTTPException, Depends, status
from database import engine, SessionLocal,get_db
import models
from typing import List
from pydantic import BaseModel
from sqlalchemy.orm import Session
import schemas, auth
from fastapi.security import OAuth2PasswordRequestForm

app = FastAPI()

models.Base.metadata.create_all(bind=engine)


class GenTask(BaseModel):
     title:str
     description:str
     is_completed:bool
    

class Create_Task(GenTask):
    pass

class Res_task(GenTask):
    id:int
    class Config():
        from_attributes = True


@app.post("/users", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: schemas.UserCreate, db: Session=Depends(get_db)):
    db_user = db.query(models.DBUser).filter(models.DBUser.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email Already Registered!")
    hashed_pwd = auth.hash_password(user.password)

    new_user = models.DBUser(
        email = user.email,
        password = hashed_pwd
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user



@app.get("/users", response_model=List[schemas.UserResponse])
def get_users(db: Session=Depends(get_db)):
    return db.query(models.DBUser).all()


@app.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db:Session=Depends(get_db)):
    user = db.query(models.DBUser).filter(models.DBUser.email == form_data.username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid Credentails",
                            headers={"WWW-Authenticate": "Bearer"},)

    if not auth.verify_password(form_data.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="incorrect password",
                            headers={"WWW-Authenticate":"Bearer"})
    access_token = auth.create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/tasks", status_code=status.HTTP_201_CREATED)
def add_task(tas: GenTask, db: Session = Depends(get_db), current_user: models.DBUser = Depends(auth.get_current_user)):
    added = models.DBTask(owner_id = current_user.id, title = tas.title, description = tas.description,is_completed= tas.is_completed)
    db.add(added)
    db.commit()
    db.refresh(added)
    return added

@app.get("/tasks", response_model=List[Res_task])
def get_tasks(db: Session = Depends(get_db), current_user: models.DBUser=Depends(auth.get_current_user)):
    user = db.query(models.DBTask).filter(models.DBTask.owner_id == current_user.id).all()
    return user

@app.get("/tasks_get_completed", response_model=List[Res_task])
def completed_task(db: Session = Depends(get_db), curr_user: models.DBUser = Depends(auth.get_current_user)):
    tasks= db.query(models.DBTask).filter(
             models.DBTask.owner_id == curr_user.id       
            ,models.DBTask.is_completed == True).all()
    if not tasks:
                raise HTTPException(status_code=400, detail="No completed tasks yet!")

    return tasks

@app.delete("/tasks_get_completed")
def completed_task(db: Session = Depends(get_db), curr_user: models.DBUser = Depends(auth.get_current_user)):
    tasks= db.query(models.DBTask).filter(
             models.DBTask.owner_id == curr_user.id
            ,models.DBTask.is_completed == True).all()
    if not tasks:
                raise HTTPException(status_code=400, detail="No completed tasks yet!")

    for task in tasks:
         db.delete(task)

    db.commit()
    return {"Message:" "All Completed tasks removed!"}
@app.put("/tasks/{tas_id}", response_model=Res_task)
def update_task(tas_id: int, new_task: Create_Task, db: Session = Depends(get_db), curr_user: models.DBUser = Depends(auth.get_current_user)):
     old_task = db.query(models.DBTask).filter(models.DBTask.id == tas_id, models.DBTask.owner_id == curr_user.id).first()
     if not old_task:
          raise HTTPException(status_code=404, detail="Task Not Found!")
     old_task.title = new_task.title
     old_task.description = new_task.description
     old_task.is_completed = new_task.is_completed
     db.commit()
     return old_task
