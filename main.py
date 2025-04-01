from init import *
import json 

app = FastAPI()

BASE_URL = "/api/"

app.mount("/media",StaticFiles(directory="media"), name="media")

@app.get("/")
async def main():
    text = "" 
    with open("index.html","r") as f:
        text = f.read()
    return HTMLResponse(content=text,status_code=200)


@app.get(BASE_URL + "list_symptoms")
async def get_symptoms():
    try:
     data = {}

     with sql.connect(PATH_DB) as conn:
       cursor = conn.cursor()
       cursor.execute(f"SELECT id,title FROM {Types}")
       ft = cursor.fetchall()
       for id_s,title in ft:
           cursor.execute(f"SELECT desc FROM {Symptoms} WHERE type_id = ?",(id_s,))
           local_symptom = cursor.fetchall()
           data[title] = local_symptom
     return {"symptoms":data}
    except sql.DatabaseError as e:
        db_error(e)


@app.get(BASE_URL + "list_diseas")
async def get_diseas():
    try:
        data = {}
        with sql.connect(PATH_DB) as conn:
            cursor = conn.cursor()
            cursor.execute(
f"""
SELECT DISTINCT d.title,s.desc
FROM {Diseas} d
LEFT JOIN DS ds ON ds.disea_id = d.id 
LEFT JOIN {Symptoms} s ON s.id = ds.symptom_id  
"""   
            )

            data_ = cursor.fetchall()
            conn.commit()
            for i in data_:
                if data.get(i[0]) is None:
                    data[i[0]] =  [ i[1] ]
                else:
                    data[i[0]].append(i[1])
        return {"diseas":data} 
    except sql.DatabaseError as e:
        db_error(e)


@app.post(BASE_URL + "add")
async def create_disea(data : DiseaCreate):
    response = createData(data)
    return response
    

@app.post(BASE_URL + "analyz")
async def analyz_symptoms(post_data : AnalyzesData):
    try:
     with sql.connect(PATH_DB) as conn:
        cursor = conn.cursor()
        
        symptoms_list = []
        for i in post_data.symptoms:
            cursor.execute(f"SELECT id FROM {Symptoms} WHERE desc = ?",(i,))
            local_data = cursor.fetchone()
            if local_data is not None:
                symptoms_list.append(local_data[0])
        

        diseases_list = None
        placeholder = ",".join('?' * len(symptoms_list))

        if symptoms_list:
            cursor.execute(
f"""
SELECT d.title, COUNT(ds.symptom_id) AS symptom_count
FROM {Diseas} d
JOIN DS ds ON d.id = ds.disea_id
WHERE ds.symptom_id IN ({placeholder})
GROUP BY d.title
ORDER BY symptom_count DESC
""",symptoms_list)
            diseases_list = cursor.fetchall()


        conn.commit()
        return {"response":diseases_list}
    except sql.Error as e:
        db_error(e)
    



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app,host="0.0.0.0",port=8000)
        

            


