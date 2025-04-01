import sqlite3 as sql 
from pydantic import BaseModel
from typing import Dict,List
from fastapi import FastAPI,HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles


PATH_DB = "db.sqlite3"

Diseas = "Diseases"
Treatments = "Treatments"


def db_error(e):
    raise HTTPException(status_code=500,detail=f"DB Error: {str(e)}")


Types = "TypesSymptoms"
Symptoms = "Symptoms"

base_id = "id INTEGER PRIMARY KEY AUTOINCREMENT"

base_create_tb_text = "CREATE TABLE IF NOT EXISTS"
base_add_tb_text = lambda table : f"INSERT INTO {table}  "
base_get_tb_text = lambda table,data : f"SELECT {data} FROM {table} "

def rel(column,table):
    return f"Foreign key ({column}) references {table}(id) "


def init_db():
    with sql.connect(PATH_DB) as db:
        cursor = db.cursor()
        
        cursor.execute(f"{base_create_tb_text} {Diseas} ( {base_id} , title TEXT , desc TEXT , rare INTEGER)  ")

        cursor.execute(f"{base_create_tb_text} {Types} ({base_id},title TEXT)")

        cursor.execute(f"{base_create_tb_text} {Symptoms} ({base_id} , desc TEXT , type_id INTEGER ,location TEXT DEFAULT 'Общая' , {rel("type_id",Types)} )")

        cursor.execute(f"{base_create_tb_text} {Treatments} ({base_id} , title TEXT , desc TEXT)")

        cursor.execute(f"{base_create_tb_text} DS ({base_id} , disea_id INTEGER , symptom_id INTEGER , {rel("disea_id",Diseas)} , {rel("symptom_id",Symptoms)})")

        cursor.execute(f"{base_create_tb_text} DT ({base_id} , disea_id INTEGER , treat_id INTEGER , {rel("disea_id",Diseas)} , {rel("treat_id",Treatments)})")
        
        db.commit()



class DiseaCreate(BaseModel):
    title: str 
    desc: str
    symptoms: Dict[str,List[str]] 
    treatments: Dict[str,str] 

class AnalyzesData(BaseModel):
    symptoms:List[str]



def createData(data):
    try:  
     with sql.connect(PATH_DB) as f:
        cursor = f.cursor()
        cursor.execute(f" {base_get_tb_text(Diseas,'id')}  WHERE title = ? ",(data.title,))
        disease_id = cursor.fetchone()
        if disease_id is None:
            cursor.execute(f"{base_add_tb_text(Diseas)} (title,desc) VALUES (?,?)",(data.title,data.desc))
            disease_id = cursor.lastrowid
        else:
            disease_id = disease_id[0]

        symptom_ids = []
        for type_symptom,symptoms  in data.symptoms.items():
            type_symptom = type_symptom.lower()
            cursor.execute(f"{base_get_tb_text( Types  , "id")} WHERE title = ? ",(type_symptom,))
            type_id = cursor.fetchone()
            if type_id is None:
                cursor.execute(f" {base_add_tb_text(Types)} (title) VALUES (?) ",(type_symptom,))
                type_id = cursor.lastrowid
            else:
                type_id = type_id[0]

            for symptom in symptoms:
                symptom = symptom.lower()
                description_symptom = f"{type_symptom} {symptom}".strip() if symptom else type_symptom
                cursor.execute(f"{base_get_tb_text(Symptoms,"id")} WHERE desc = ? and type_id = ? ",(description_symptom.lower(),type_id))

                symptom_id = cursor.fetchone()
                if symptom_id is None:
                    cursor.execute(f"{base_add_tb_text(Symptoms)} (desc,type_id,location) VALUES(?,?,?)",(description_symptom,type_id,symptom or None))
                    symptom_id = cursor.lastrowid
                else:
                    symptom_id = symptom_id[0]

                symptom_ids.append(symptom_id)


            treatmen_ids = []
            for treat,desc_tret in data.treatments.items():
                cursor.execute(f"{base_get_tb_text(Treatments,"id")} WHERE title = ? ",(treat,))
                treatment_id = cursor.fetchone()
                if treatment_id is None:
                    cursor.execute(f"{base_add_tb_text(Treatments)} (title,desc) VALUES (?,?)",(treat,desc_tret,))
                    treatment_id = cursor.lastrowid
                else:
                    treatment_id = treatment_id[0]

                treatmen_ids.append(treatment_id)

            for sympt_id in symptom_ids:
                cursor.execute(f"INSERT OR IGNORE INTO DS (disea_id,symptom_id) VALUES (?,?) ",(disease_id,symptom_id,))


            for treat_id in treatmen_ids:
                cursor.execute(f"INSERT OR IGNORE INTO DT (disea_id,treat_id) VALUES (?,?)",(disease_id,treat_id,))

            f.commit()

        return  {"message": f"Disease '{data.title}' added successfully", "disease_id": disease_id}
    except sql.DatabaseError as e:
        db_error(e)




if __name__ == "__main__":
    init_db()